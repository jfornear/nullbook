from django.conf import settings
from django.db import models


class AmazonOrder(models.Model):
    """Amazon order from the 'Request My Data' export, used for cross-referencing."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="amazon_orders")
    order_date = models.DateField()
    order_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=500)
    asin = models.CharField(max_length=20, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=200, blank=True)
    matched_transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="amazon_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.order_date} - {self.product_name[:50]} (${self.total_amount})"


class ImportBatch(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("preview", "Preview"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="import_batches")
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="import_batches", null=True, blank=True)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    row_count = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)
    column_mapping = models.JSONField(default=dict, blank=True, help_text="Maps CSV columns to transaction fields")
    bank_profile = models.CharField(max_length=50, blank=True, help_text="Detected bank profile ID")
    source_institution = models.CharField(max_length=100, blank=True, help_text="Bank or institution name")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "import batches"

    def __str__(self):
        return f"{self.file_name} ({self.status})"
