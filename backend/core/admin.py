from django.contrib import admin

from .models import Alert, UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ["user", "currency", "fiscal_year_start", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["title", "alert_type", "severity", "user", "is_read", "created_at"]
    list_filter = ["alert_type", "severity", "is_read"]
    search_fields = ["title", "message"]
