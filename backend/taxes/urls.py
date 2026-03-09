from rest_framework.routers import DefaultRouter

from .views import DeductibleExpenseViewSet, ReceiptViewSet, TaxDocumentViewSet, TaxYearViewSet

router = DefaultRouter()
router.register(r"tax-years", TaxYearViewSet, basename="tax-year")
router.register(r"tax-documents", TaxDocumentViewSet, basename="tax-document")
router.register(r"deductions", DeductibleExpenseViewSet, basename="deduction")
router.register(r"receipts", ReceiptViewSet, basename="receipt")

urlpatterns = router.urls
