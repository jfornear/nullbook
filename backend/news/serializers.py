from rest_framework import serializers

from .models import NewsArticle, NewsSource, Watchlist


class NewsSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsSource
        fields = [
            "id",
            "name",
            "url",
            "feed_url",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NewsArticleSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "source",
            "source_name",
            "title",
            "url",
            "summary",
            "published_at",
            "is_read",
            "is_bookmarked",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = [
            "id",
            "name",
            "keywords",
            "sources",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
