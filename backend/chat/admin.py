from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "is_pinned", "is_archived", "created_at"]
    list_filter = ["is_pinned", "is_archived", "created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "created_at"]
    list_filter = ["role", "created_at"]
