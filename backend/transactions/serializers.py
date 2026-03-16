from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import Budget, Category, CategoryRule, Goal, Subscription, Tag, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent", "icon", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    category_detail = CategorySerializer(source="category", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.none(),
        many=True,
        write_only=True,
        required=False,
        source="tags",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            self.fields["tag_ids"].child_relation.queryset = Tag.objects.filter(user=request.user)

    def validate_account(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid account.")
        return value

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "category",
            "category_name",
            "category_detail",
            "tags",
            "tags_detail",
            "tag_ids",
            "date",
            "amount",
            "transaction_type",
            "description",
            "notes",
            "is_recurring",
            "import_batch",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "tags": {"read_only": True},
        }


class CategoryRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CategoryRule
        fields = ["id", "pattern", "category", "category_name", "auto_generated", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class GoalSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    account_name = serializers.CharField(source="linked_account.name", read_only=True, default=None)
    progress_pct = serializers.FloatField(read_only=True)

    def validate_linked_account(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid account.")
        return value

    class Meta:
        model = Goal
        fields = [
            "id", "name", "target_amount", "current_amount", "target_date",
            "category", "category_name", "linked_account", "account_name",
            "progress_pct", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default="Total")
    spent = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            "id", "category", "category_name", "amount", "period",
            "is_active", "spent", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_spent(self, obj):
        # Use pre-computed value if available (set by progress action to avoid N+1)
        if hasattr(obj, "_precomputed_spent"):
            return str(obj._precomputed_spent)

        now = timezone.now()
        if obj.period == "weekly":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif obj.period == "annual":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # monthly
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        qs = Transaction.objects.filter(
            user=obj.user,
            transaction_type="expense",
            date__gte=start.date(),
        )
        if obj.category:
            qs = qs.filter(category=obj.category)
        total = qs.aggregate(total=Sum("amount"))["total"]
        return str(total or 0)


class SubscriptionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    annual_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "merchant", "amount", "frequency", "category", "category_name",
            "status", "confidence", "last_charged", "next_expected",
            "cancellation_url", "cancellation_method", "notes",
            "annual_cost", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "confidence", "created_at", "updated_at"]
