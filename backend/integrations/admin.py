from django.contrib import admin

from .models import PlaidItem, PlaidSyncCursor


@admin.register(PlaidItem)
class PlaidItemAdmin(admin.ModelAdmin):
    list_display = [
        "institution_name",
        "user",
        "status",
        "institution_id",
        "last_synced_at",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = ["institution_name", "user__username", "item_id"]
    readonly_fields = ["item_id", "created_at", "updated_at"]


@admin.register(PlaidSyncCursor)
class PlaidSyncCursorAdmin(admin.ModelAdmin):
    list_display = [
        "plaid_item",
        "account_id",
        "local_account",
        "updated_at",
    ]
    search_fields = ["account_id", "plaid_item__institution_name"]
    readonly_fields = ["created_at", "updated_at"]
