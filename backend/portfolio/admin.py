from django.contrib import admin

from .models import Holding, PriceHistory, Security, TradeHistory


@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ["symbol", "name", "security_type", "exchange", "currency"]
    list_filter = ["security_type", "exchange", "currency"]
    search_fields = ["symbol", "name"]


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ["user", "account", "security", "shares", "cost_basis", "updated_at"]
    list_filter = ["security__security_type"]
    search_fields = ["security__symbol", "security__name", "user__username"]
    raw_id_fields = ["user", "account", "security"]


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ["security", "date", "open_price", "close_price", "high_price", "low_price", "volume"]
    list_filter = ["date"]
    search_fields = ["security__symbol"]
    raw_id_fields = ["security"]


@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "security", "date", "trade_type", "shares", "price_per_share", "fees"]
    list_filter = ["trade_type", "date"]
    search_fields = ["security__symbol", "user__username", "notes"]
    raw_id_fields = ["user", "account", "security"]
