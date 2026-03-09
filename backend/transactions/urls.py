from rest_framework.routers import DefaultRouter

from .views import BudgetViewSet, CategoryRuleViewSet, CategoryViewSet, GoalViewSet, SubscriptionViewSet, TagViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(r"goals", GoalViewSet, basename="goal")
router.register(r"category-rules", CategoryRuleViewSet, basename="category-rule")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = router.urls
