from django.conf import settings
from django.db import models


class NewsSource(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    feed_url = models.URLField(blank=True, help_text="RSS/Atom feed URL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name="articles")
    title = models.CharField(max_length=500)
    url = models.URLField()
    summary = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlists")
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Comma-separated keywords to monitor")
    sources = models.ManyToManyField(NewsSource, blank=True, related_name="watchlists")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
