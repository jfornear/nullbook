import logging

import feedparser
from celery import shared_task
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


def parse_published(entry):
    """Extract a timezone-aware datetime from a feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, attr, None)
        if tp:
            from datetime import datetime

            dt = datetime(*tp[:6], tzinfo=timezone.utc)
            return dt
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            dt = parse_datetime(val)
            if dt:
                return dt if timezone.is_aware(dt) else timezone.make_aware(dt)
    return None


def fetch_articles_for_source(source):
    """Fetch and store new articles from a single NewsSource. Returns count of new articles."""
    from .models import NewsArticle

    if not source.feed_url:
        return 0

    feed = feedparser.parse(source.feed_url)
    if feed.bozo and not feed.entries:
        logger.warning("Failed to parse feed for %s: %s", source.name, feed.bozo_exception)
        return 0

    existing_urls = set(
        NewsArticle.objects.filter(source=source).values_list("url", flat=True)
    )

    new_articles = []
    for entry in feed.entries:
        url = entry.get("link", "")
        if not url or url in existing_urls:
            continue

        new_articles.append(
            NewsArticle(
                source=source,
                title=entry.get("title", "")[:500],
                url=url,
                summary=entry.get("summary", ""),
                published_at=parse_published(entry) or timezone.now(),
            )
        )

    if new_articles:
        NewsArticle.objects.bulk_create(new_articles, ignore_conflicts=True)

    logger.info("Fetched %d new articles from %s", len(new_articles), source.name)
    return len(new_articles)


@shared_task
def fetch_news_articles():
    """Fetch latest articles from all active news sources."""
    from .models import NewsSource

    active_sources = NewsSource.objects.filter(is_active=True)
    total = 0
    for source in active_sources:
        try:
            total += fetch_articles_for_source(source)
        except Exception:
            logger.exception("Error fetching articles for %s", source.name)
    return f"Fetched {total} new articles from {active_sources.count()} sources"


@shared_task
def fetch_single_source(source_id):
    """Fetch articles for a single source by ID."""
    from .models import NewsSource

    try:
        source = NewsSource.objects.get(id=source_id)
    except NewsSource.DoesNotExist:
        return
    fetch_articles_for_source(source)
