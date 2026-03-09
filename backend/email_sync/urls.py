from rest_framework.routers import DefaultRouter

from .views import EmailAccountViewSet, EmailMessageViewSet, EmailRuleViewSet

router = DefaultRouter()
router.register(r"accounts", EmailAccountViewSet, basename="email-account")
router.register(r"rules", EmailRuleViewSet, basename="email-rule")
router.register(r"messages", EmailMessageViewSet, basename="email-message")

urlpatterns = router.urls
