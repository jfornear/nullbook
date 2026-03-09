import json

from django.conf import settings
from django.db import models

from core.encryption import get_fernet as _get_fernet


class EmailAccount(models.Model):
    """A connected email account via IMAP."""

    PROVIDER_CHOICES = [
        ("imap", "IMAP"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("error", "Error"),
        ("disconnected", "Disconnected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_accounts",
    )
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES)
    email_address = models.EmailField()
    _credentials = models.TextField(
        db_column="credentials",
        default="",
        help_text="Encrypted IMAP credentials (JSON)",
    )
    imap_host = models.CharField(max_length=255, blank=True)
    imap_port = models.IntegerField(default=993)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "email_address"]

    def __str__(self):
        return f"{self.email_address} ({self.get_provider_display()})"

    @property
    def credentials(self):
        """Decrypt and return stored credentials as a dict."""
        if not self._credentials:
            return {}
        f = _get_fernet()
        decrypted = f.decrypt(self._credentials.encode("utf-8")).decode("utf-8")
        return json.loads(decrypted)

    @credentials.setter
    def credentials(self, value):
        """Encrypt and store credentials dict."""
        if not value:
            self._credentials = ""
            return
        f = _get_fernet()
        serialized = json.dumps(value)
        self._credentials = f.encrypt(serialized.encode("utf-8")).decode("utf-8")


class EmailRule(models.Model):
    """A rule for matching and processing incoming emails."""

    ACTION_CHOICES = [
        ("process_receipt", "Process as Receipt"),
        ("ignore", "Ignore"),
        ("archive", "Archive"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_rules",
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    from_pattern = models.CharField(
        max_length=500,
        blank=True,
        help_text="Regex or substring to match sender email/name",
    )
    subject_pattern = models.CharField(
        max_length=500,
        blank=True,
        help_text="Regex or substring to match subject line",
    )
    has_attachment = models.BooleanField(
        null=True,
        blank=True,
        help_text="True = must have attachment, False = must not, None = either",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority rules are checked first",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_action_display()})"


class EmailMessage(models.Model):
    """Record of a processed email message."""

    email_account = models.ForeignKey(
        EmailAccount,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    message_id = models.CharField(
        max_length=500,
        unique=True,
        help_text="Email Message-ID header",
    )
    from_address = models.CharField(max_length=500)
    subject = models.CharField(max_length=1000)
    date = models.DateTimeField()
    matched_rule = models.ForeignKey(
        EmailRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matched_messages",
    )
    is_processed = models.BooleanField(default=False)
    action_taken = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.from_address}: {self.subject[:80]}"


class EmailAttachment(models.Model):
    """An attachment extracted from a processed email."""

    email_message = models.ForeignKey(
        EmailMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=200)
    file = models.FileField(upload_to="email_attachments/%Y/%m/")
    receipt = models.ForeignKey(
        "taxes.Receipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_attachments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.filename
