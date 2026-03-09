from django.contrib import admin

from .models import Account, BalanceHistory, Institution


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ["name", "institution_type", "website", "created_at"]
    list_filter = ["institution_type"]
    search_fields = ["name"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "institution", "account_type", "balance", "currency", "is_active", "updated_at"]
    list_filter = ["account_type", "is_active", "currency"]
    search_fields = ["name", "user__username"]


@admin.register(BalanceHistory)
class BalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ["account", "date", "balance", "created_at"]
    list_filter = ["date"]
    search_fields = ["account__name"]
