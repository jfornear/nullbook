from django.conf import settings
from django.db import models


class Institution(models.Model):
    name = models.CharField(max_length=200)
    institution_type = models.CharField(
        max_length=20,
        choices=[
            ("bank", "Bank"),
            ("credit_union", "Credit Union"),
            ("brokerage", "Brokerage"),
            ("crypto", "Crypto Exchange"),
            ("other", "Other"),
        ],
        default="bank",
    )
    website = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("checking", "Checking"),
        ("savings", "Savings"),
        ("credit_card", "Credit Card"),
        ("investment", "Investment"),
        ("loan", "Loan"),
        ("mortgage", "Mortgage"),
        ("cash", "Cash"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name="accounts")
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default="checking")
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class BalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="balance_history")
    date = models.DateField()
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ["account", "date"]
        verbose_name_plural = "balance histories"

    def __str__(self):
        return f"{self.account.name} - {self.date}: {self.balance}"
