"""Celery tasks for portfolio automation."""

import logging
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def update_security_prices():
    """Fetch latest prices for all held securities using yfinance.

    Runs daily after market close via Celery beat.
    """
    from portfolio.models import Holding, PriceHistory, Security

    # Get all unique securities that users hold
    held_security_ids = Holding.objects.values_list("security_id", flat=True).distinct()
    securities = Security.objects.filter(id__in=held_security_ids)

    if not securities.exists():
        return "No securities to update"

    symbols = [s.symbol for s in securities]
    symbol_to_security = {s.symbol: s for s in securities}

    try:
        import yfinance as yf

        updated = 0

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                security = symbol_to_security[symbol]

                # Fetch last 5 trading days so we have a previous close for day change
                hist = ticker.history(period="5d")
                if hist.empty:
                    continue

                for row_date, row in hist.iterrows():
                    day = row_date.date()
                    close = row.get("Close")
                    if close is None:
                        continue
                    PriceHistory.objects.update_or_create(
                        security=security,
                        date=day,
                        defaults={
                            "close_price": Decimal(str(round(close, 4))),
                            "open_price": Decimal(str(round(row.get("Open", close), 4))),
                            "high_price": Decimal(str(round(row.get("High", close), 4))),
                            "low_price": Decimal(str(round(row.get("Low", close), 4))),
                            "volume": int(row.get("Volume", 0)) or None,
                        },
                    )

                updated += 1
                logger.info("Updated prices for %s (%d days)", symbol, len(hist))

            except Exception:
                logger.exception("Failed to update price for %s", symbol)

        return f"Updated prices for {updated}/{len(symbols)} securities"

    except ImportError:
        logger.error("yfinance not installed")
        return "yfinance not installed"
    except Exception:
        logger.exception("Price update failed")
        return "Price update failed"
