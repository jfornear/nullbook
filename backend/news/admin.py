from django.contrib import admin

from .models import NewsArticle, NewsSource, Watchlist


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "url"]


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "source", "published_at", "is_read", "is_bookmarked", "created_at"]
    list_filter = ["is_read", "is_bookmarked", "source"]
    search_fields = ["title", "summary"]


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "keywords"]
