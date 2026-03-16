from django.conf import settings
from django.db import models


class Security(models.Model):
    SECURITY_TYPES = [
        ("stock", "Stock"),
        ("etf", "ETF"),
        ("mutual_fund", "Mutual Fund"),
        ("bond", "Bond"),
        ("crypto", "Cryptocurrency"),
        ("option", "Option"),
        ("other", "Other"),
    ]

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    security_type = models.CharField(max_length=20, choices=SECURITY_TYPES, default="stock")
    exchange = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        verbose_name_plural = "securities"

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Holding(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holdings")
    account = models.ForeignKey("accounts.Account", on_delete=models.SET_NULL, null=True, blank=True, related_name="holdings")
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name="holdings")
    shares = models.DecimalField(max_digits=14, decimal_places=6)
    cost_basis = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["security__symbol"]
        constraints = [
            models.UniqueConstraint(fields=["user", "account", "security"], name="unique_user_account_security"),
        ]

    def __str__(self):
        return f"{self.security.symbol}: {self.shares} shares"


class PriceHistory(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name="price_history")
    date = models.DateField()
    open_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    close_price = models.DecimalField(max_digits=14, decimal_places=4)
    high_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "price histories"
        constraints = [
            models.UniqueConstraint(fields=["security", "date"], name="unique_security_price_date"),
        ]

    def __str__(self):
        return f"{self.security.symbol} {self.date}: {self.close_price}"


class CryptoTaxLot(models.Model):
    """Tax lot for crypto dispositions — tracks cost basis and gains/losses."""

    HOLDING_PERIODS = [
        ("short_term", "Short-Term"),
        ("long_term", "Long-Term"),
        ("unknown", "Unknown"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_tax_lots")
    asset = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    cost_basis = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_acquired = models.DateField(null=True, blank=True)
    date_disposed = models.DateField(null=True, blank=True)
    proceeds = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gain_loss = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    holding_period = models.CharField(max_length=20, choices=HOLDING_PERIODS, default="unknown")
    source = models.CharField(max_length=50, blank=True, help_text="e.g., 'coinbase', '1099-da'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_disposed"]

    def __str__(self):
        return f"{self.asset} {self.quantity} — {self.holding_period} gain: ${self.gain_loss}"

    @property
    def is_gain(self):
        return self.gain_loss > 0


class TradeHistory(models.Model):
    TRADE_TYPES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
        ("dividend", "Dividend"),
        ("split", "Split"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trades")
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="trades")
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name="trades")
    date = models.DateField()
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    shares = models.DecimalField(max_digits=14, decimal_places=6)
    price_per_share = models.DecimalField(max_digits=14, decimal_places=4)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "trade histories"

    def __str__(self):
        return f"{self.trade_type} {self.shares} {self.security.symbol} @ {self.price_per_share}"
