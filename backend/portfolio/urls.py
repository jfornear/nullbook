from rest_framework.routers import DefaultRouter

from .views import HoldingViewSet, PriceHistoryViewSet, SecurityViewSet, TradeHistoryViewSet

router = DefaultRouter()
router.register(r"securities", SecurityViewSet, basename="security")
router.register(r"holdings", HoldingViewSet, basename="holding")
router.register(r"price-history", PriceHistoryViewSet, basename="price-history")
router.register(r"trades", TradeHistoryViewSet, basename="trade")

urlpatterns = router.urls
