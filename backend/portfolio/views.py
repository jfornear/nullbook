import logging
from collections import defaultdict
from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Holding, PriceHistory, Security, TradeHistory
from .serializers import (
    HoldingSerializer,
    PriceHistorySerializer,
    SecuritySerializer,
    TradeHistorySerializer,
)

logger = logging.getLogger(__name__)


QUOTE_TYPE_MAP = {
    "EQUITY": "stock",
    "ETF": "etf",
    "MUTUALFUND": "mutual_fund",
    "CRYPTOCURRENCY": "crypto",
}


class SecurityViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for securities (created via lookup action or system)."""

    queryset = Security.objects.all()
    serializer_class = SecuritySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["symbol"]

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        """Look up a security by symbol via yfinance, upsert, and return with current_price."""
        symbol = request.query_params.get("symbol", "").strip().upper()
        if not symbol:
            return Response({"detail": "symbol query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info
        except Exception:
            logger.exception("yfinance lookup failed for %s", symbol)
            return Response({"detail": "Stock data service is temporarily unavailable."}, status=status.HTTP_502_BAD_GATEWAY)

        # yfinance returns {"trailingPegRatio": None} for unknown symbols
        if not info.get("shortName") and not info.get("longName"):
            return Response({"detail": f"Unknown symbol: {symbol}"}, status=status.HTTP_404_NOT_FOUND)

        security_type = QUOTE_TYPE_MAP.get(info.get("quoteType", ""), "other")
        name = info.get("longName") or info.get("shortName") or symbol
        exchange = info.get("exchange", "")

        security, _created = Security.objects.update_or_create(
            symbol=symbol,
            defaults={
                "name": name,
                "security_type": security_type,
                "exchange": exchange,
            },
        )

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        data = SecuritySerializer(security).data
        data["current_price"] = str(current_price) if current_price else None
        return Response(data)


class HoldingViewSet(viewsets.ModelViewSet):
    """ViewSet for user holdings."""

    serializer_class = HoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Holding.objects.filter(user=self.request.user).select_related("security")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def allocation(self, request):
        """Returns holdings grouped by security_type with total value."""
        holdings = self.get_queryset().select_related("security")
        allocation = defaultdict(lambda: {"total_shares": Decimal("0"), "total_cost_basis": Decimal("0"), "count": 0})

        for holding in holdings:
            sec_type = holding.security.security_type
            allocation[sec_type]["total_shares"] += holding.shares
            allocation[sec_type]["total_cost_basis"] += holding.cost_basis
            allocation[sec_type]["count"] += 1

        result = []
        for sec_type, data in allocation.items():
            result.append(
                {
                    "security_type": sec_type,
                    "count": data["count"],
                    "total_shares": str(data["total_shares"]),
                    "total_cost_basis": str(data["total_cost_basis"]),
                }
            )

        return Response(result)

    @action(detail=False, methods=["get"])
    def performance(self, request):
        """Returns portfolio performance with market values and gains/losses."""
        from portfolio.performance import calculate_portfolio_performance
        result = calculate_portfolio_performance(request.user)
        return Response(result)


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for price history (populated by system)."""

    queryset = PriceHistory.objects.all().select_related("security")
    serializer_class = PriceHistorySerializer
    permission_classes = [IsAuthenticated]


class TradeHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for user trade history."""

    serializer_class = TradeHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TradeHistory.objects.filter(user=self.request.user).select_related("security")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
