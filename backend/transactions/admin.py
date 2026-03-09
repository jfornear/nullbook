from django.contrib import admin

from .models import Category, CategoryRule, Subscription, Tag, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "icon", "created_at"]
    list_filter = ["parent"]
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "color"]
    list_filter = ["user"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["date", "description", "amount", "transaction_type", "category", "user"]
    list_filter = ["transaction_type", "category", "date", "is_recurring"]
    search_fields = ["description", "notes"]
    date_hierarchy = "date"


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    list_display = ["pattern", "category", "user", "auto_generated", "created_at"]
    list_filter = ["category", "auto_generated"]
    search_fields = ["pattern"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["merchant", "amount", "frequency", "status", "user", "last_charged"]
    list_filter = ["status", "frequency"]
    search_fields = ["merchant"]
