from django.conf import settings
from django.db import models

from core.encryption import get_fernet as _get_fernet


class PlaidItem(models.Model):
    """Represents a connected bank institution via Plaid."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("error", "Error"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plaid_items",
    )
    item_id = models.CharField(max_length=255, unique=True, help_text="Plaid item_id")
    _access_token = models.TextField(
        db_column="access_token",
        help_text="Encrypted Plaid access token",
    )
    plaid_institution_id = models.CharField(max_length=255, help_text="Plaid institution ID")
    institution_name = models.CharField(max_length=255)
    institution = models.ForeignKey(
        "accounts.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plaid_items",
        help_text="Link to local Institution record",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    consent_expires_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.institution_name} ({self.status})"

    @property
    def access_token(self):
        """Decrypt and return the access token."""
        if not self._access_token:
            return ""
        f = _get_fernet()
        return f.decrypt(self._access_token.encode("utf-8")).decode("utf-8")

    @access_token.setter
    def access_token(self, value):
        """Encrypt and store the access token."""
        if not value:
            self._access_token = ""
            return
        f = _get_fernet()
        self._access_token = f.encrypt(value.encode("utf-8")).decode("utf-8")


class PlaidSyncCursor(models.Model):
    """Per-account sync cursor for Plaid incremental transaction sync."""

    plaid_item = models.ForeignKey(
        PlaidItem,
        on_delete=models.CASCADE,
        related_name="sync_cursors",
    )
    account_id = models.CharField(max_length=255, help_text="Plaid account_id")
    local_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plaid_sync_cursors",
    )
    cursor = models.TextField(blank=True, help_text="Plaid sync cursor for incremental sync")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ["plaid_item", "account_id"]

    def __str__(self):
        return f"{self.plaid_item.institution_name} - {self.account_id}"
