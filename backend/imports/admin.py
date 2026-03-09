from django.contrib import admin

from .models import ImportBatch


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ["file_name", "user", "account", "status", "row_count", "imported_count", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["file_name"]
    readonly_fields = ["created_at", "updated_at"]
