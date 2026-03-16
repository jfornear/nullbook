from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    currency = models.CharField(max_length=3, default="USD")
    fiscal_year_start = models.PositiveSmallIntegerField(
        default=1,
        help_text="Month number (1-12)",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "user settings"

    def __str__(self):
        return f"Settings for {self.user.username}"


class Alert(models.Model):
    ALERT_TYPES = [
        ("unusual_spending", "Unusual Spending"),
        ("bill_due", "Bill Due"),
        ("low_balance", "Low Balance"),
        ("price_increase", "Subscription Price Increase"),
        ("large_transaction", "Large Transaction"),
        ("new_fee", "New Fee Detected"),
        ("subscription_cancelled", "Subscription Cancelled"),
        ("receipt_processed", "Receipt Processed"),
        ("tax_reminder", "Tax Reminder"),
        ("general", "General"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("urgent", "Urgent"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="info", db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    action_url = models.CharField(max_length=500, blank=True, help_text="Frontend route or external URL")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity}] {self.title}"
