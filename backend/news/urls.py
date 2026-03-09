from rest_framework.routers import DefaultRouter

from .views import NewsArticleViewSet, NewsSourceViewSet, WatchlistViewSet

router = DefaultRouter()
router.register(r"sources", NewsSourceViewSet, basename="newssource")
router.register(r"articles", NewsArticleViewSet, basename="newsarticle")
router.register(r"watchlists", WatchlistViewSet, basename="watchlist")

urlpatterns = router.urls
