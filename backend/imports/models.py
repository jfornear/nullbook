from django.conf import settings
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "import batches"

    def __str__(self):
        return f"{self.file_name} ({self.status})"
