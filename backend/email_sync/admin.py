from django.contrib import admin

from .models import EmailAccount, EmailAttachment, EmailMessage, EmailRule


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "email_address", "provider", "status", "last_synced_at"]
    list_filter = ["provider", "status"]
    search_fields = ["email_address", "user__username"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EmailRule)
class EmailRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "action", "priority", "is_active"]
    list_filter = ["action", "is_active"]
    search_fields = ["name", "from_pattern", "subject_pattern"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ["from_address", "subject", "date", "is_processed", "action_taken"]
    list_filter = ["is_processed", "email_account"]
    search_fields = ["from_address", "subject", "message_id"]
    readonly_fields = ["created_at"]


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ["filename", "content_type", "email_message", "receipt"]
    list_filter = ["content_type"]
    search_fields = ["filename"]
    readonly_fields = ["created_at"]
