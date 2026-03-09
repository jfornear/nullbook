import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NewsArticle, NewsSource, Watchlist
from .serializers import NewsArticleSerializer, NewsSourceSerializer, WatchlistSerializer
from .tasks import fetch_articles_for_source

logger = logging.getLogger(__name__)


class NewsSourceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """News sources: read + create only (no update/delete of shared data)."""

    queryset = NewsSource.objects.all()
    serializer_class = NewsSourceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        source = serializer.save()
        try:
            fetch_articles_for_source(source)
        except Exception:
            logger.exception("Failed initial fetch for %s", source.name)

    @action(detail=True, methods=["post"])
    def fetch(self, request, pk=None):
        source = self.get_object()
        try:
            count = fetch_articles_for_source(source)
        except Exception:
            logger.exception("Failed to fetch articles for %s", source.name)
            return Response(
                {"error": "Failed to fetch articles"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"fetched": count})

    @action(detail=False, methods=["post"])
    def fetch_all(self, request):
        from .tasks import fetch_news_articles
        fetch_news_articles.delay()
        return Response({"status": "queued", "message": "News fetch started in background."})


class NewsArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for news articles (fetched automatically from sources)."""

    queryset = NewsArticle.objects.select_related("source").all()
    serializer_class = NewsArticleSerializer
    permission_classes = [IsAuthenticated]


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
