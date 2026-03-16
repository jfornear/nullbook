from rest_framework.routers import DefaultRouter

from .views import AmazonOrderViewSet, ImportBatchViewSet

router = DefaultRouter()
router.register(r"batches", ImportBatchViewSet, basename="import-batch")
router.register(r"amazon-orders", AmazonOrderViewSet, basename="amazon-order")

urlpatterns = router.urls
