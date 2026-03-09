"""Portfolio performance calculations.

Computes unrealized gains/losses, day change, and portfolio performance
using price history data, with live quote fallback via yfinance.
"""

import logging
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

LIVE_QUOTES_CACHE_KEY = "portfolio_live_quotes"
LIVE_QUOTES_CACHE_TTL = 300  # seconds (5 minutes)


def _fetch_live_quotes(symbols: list[str]) -> dict[str, Decimal]:
    """Fetch live quotes for symbols via yfinance, cached for 60s."""
    cached = cache.get(LIVE_QUOTES_CACHE_KEY)
    if cached is not None:
        return cached

    quotes = {}
    try:
        import yfinance as yf

        tickers = yf.Tickers(" ".join(symbols))
        for symbol in symbols:
            try:
                info = tickers.tickers[symbol].info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price is not None:
                    quotes[symbol] = Decimal(str(price))
            except Exception:
                logger.debug("Failed to get live quote for %s", symbol)
    except Exception:
        logger.exception("yfinance batch quote fetch failed")

    cache.set(LIVE_QUOTES_CACHE_KEY, quotes, LIVE_QUOTES_CACHE_TTL)
    return quotes


def calculate_portfolio_performance(user) -> dict:
    """Calculate portfolio performance metrics for a user.

    Returns:
        {
            "total_market_value": Decimal,
            "total_cost_basis": Decimal,
            "total_unrealized_gain": Decimal,
            "total_unrealized_gain_pct": float,
            "day_change": Decimal,
            "day_change_pct": float,
            "holdings": [...],
        }
    """
    from portfolio.models import Holding, PriceHistory

    holdings = Holding.objects.filter(user=user).select_related("security")

    if not holdings.exists():
        return {
            "total_market_value": "0.00",
            "total_cost_basis": "0.00",
            "total_unrealized_gain": "0.00",
            "total_unrealized_gain_pct": 0,
            "day_change": "0.00",
            "day_change_pct": 0,
            "holdings": [],
        }

    from django.db.models import Max, Q

    security_ids = [h.security_id for h in holdings]
    symbol_to_sid = {h.security.symbol: h.security_id for h in holdings}
    today = timezone.now().date()

    # Latest date per security (1 query)
    latest_date_map = dict(
        PriceHistory.objects.filter(security_id__in=security_ids, date__lte=today)
        .values("security_id")
        .annotate(max_date=Max("date"))
        .values_list("security_id", "max_date")
    )

    latest_prices = {}
    previous_prices = {}

    if latest_date_map:
        # Fetch latest price rows (1 query)
        latest_q = Q()
        for sid, d in latest_date_map.items():
            latest_q |= Q(security_id=sid, date=d)
        for ph in PriceHistory.objects.filter(latest_q):
            latest_prices[ph.security_id] = ph.close_price

        # Previous date per security (1 query)
        prev_q = Q()
        for sid, d in latest_date_map.items():
            prev_q |= Q(security_id=sid, date__lt=d)
        prev_date_map = dict(
            PriceHistory.objects.filter(prev_q)
            .values("security_id")
            .annotate(max_date=Max("date"))
            .values_list("security_id", "max_date")
        )

        # Fetch previous price rows (1 query)
        if prev_date_map:
            prev_price_q = Q()
            for sid, d in prev_date_map.items():
                prev_price_q |= Q(security_id=sid, date=d)
            for ph in PriceHistory.objects.filter(prev_price_q):
                previous_prices[ph.security_id] = ph.close_price

    # Fetch live quotes to supplement stale PriceHistory data
    stale_symbols = [
        sym for sym, sid in symbol_to_sid.items()
        if latest_date_map.get(sid) is None or latest_date_map[sid] < today
    ]
    if stale_symbols:
        live_quotes = _fetch_live_quotes(stale_symbols)
        for sym, price in live_quotes.items():
            sid = symbol_to_sid.get(sym)
            if sid is not None:
                # Use existing close as previous, live as current
                if sid in latest_prices:
                    previous_prices.setdefault(sid, latest_prices[sid])
                latest_prices[sid] = price

    total_market_value = Decimal("0")
    total_cost_basis = Decimal("0")
    total_prev_value = Decimal("0")
    holding_details = []

    for h in holdings:
        current_price = latest_prices.get(h.security_id)
        prev_price = previous_prices.get(h.security_id)

        if current_price:
            market_value = h.shares * current_price
            unrealized_gain = market_value - h.cost_basis
            gain_pct = (float(unrealized_gain) / float(h.cost_basis) * 100) if h.cost_basis else 0

            day_change = Decimal("0")
            day_change_pct = 0.0
            if prev_price:
                prev_value = h.shares * prev_price
                day_change = market_value - prev_value
                day_change_pct = (float(current_price - prev_price) / float(prev_price) * 100) if prev_price else 0
                total_prev_value += prev_value
            else:
                total_prev_value += market_value
        else:
            market_value = h.cost_basis
            unrealized_gain = Decimal("0")
            gain_pct = 0
            day_change = Decimal("0")
            day_change_pct = 0
            total_prev_value += market_value

        total_market_value += market_value
        total_cost_basis += h.cost_basis

        holding_details.append({
            "id": h.id,
            "symbol": h.security.symbol,
            "name": h.security.name,
            "shares": str(h.shares),
            "cost_basis": str(h.cost_basis),
            "current_price": str(current_price) if current_price else None,
            "market_value": str(market_value),
            "unrealized_gain": str(unrealized_gain),
            "unrealized_gain_pct": round(gain_pct, 2),
            "day_change": str(day_change),
            "day_change_pct": round(day_change_pct, 2),
        })

    total_unrealized = total_market_value - total_cost_basis
    total_gain_pct = (float(total_unrealized) / float(total_cost_basis) * 100) if total_cost_basis else 0
    total_day_change = total_market_value - total_prev_value
    total_day_pct = (float(total_day_change) / float(total_prev_value) * 100) if total_prev_value else 0

    return {
        "total_market_value": str(total_market_value),
        "total_cost_basis": str(total_cost_basis),
        "total_unrealized_gain": str(total_unrealized),
        "total_unrealized_gain_pct": round(total_gain_pct, 2),
        "day_change": str(total_day_change),
        "day_change_pct": round(total_day_pct, 2),
        "holdings": holding_details,
    }
