from rest_framework.routers import DefaultRouter

from .views import NewsArticleViewSet, NewsSourceViewSet, WatchlistViewSet

router = DefaultRouter()
router.register(r"sources", NewsSourceViewSet, basename="news-source")
router.register(r"articles", NewsArticleViewSet, basename="news-article")
router.register(r"watchlists", WatchlistViewSet, basename="watchlist")

urlpatterns = router.urls
