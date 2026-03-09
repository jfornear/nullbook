from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, BalanceHistoryViewSet, InstitutionViewSet

router = DefaultRouter()
router.register(r"institutions", InstitutionViewSet, basename="institution")
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"balance-history", BalanceHistoryViewSet, basename="balance-history")

urlpatterns = router.urls
