import csv
import io

from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Budget, Category, CategoryRule, Goal, Subscription, Tag, Transaction
from .serializers import (
    BudgetSerializer,
    CategoryRuleSerializer,
    CategorySerializer,
    GoalSerializer,
    SubscriptionSerializer,
    TagSerializer,
    TransactionSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing transaction categories (read-only shared data)."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user-specific tags."""

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing transactions with filtering and spending summary."""

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related(
            "category", "account"
        ).prefetch_related("tags")

        # Filter by account
        account = self.request.query_params.get("account")
        if account:
            queryset = queryset.filter(account_id=account)

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        # Filter by transaction type
        transaction_type = self.request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Search on description
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(description__icontains=search)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Export transactions as CSV with current filters applied."""
        from django.http import StreamingHttpResponse

        queryset = self.get_queryset()

        def generate_csv():
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["Date", "Description", "Amount", "Category", "Account", "Type", "Tags"])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)
            for txn in queryset[:50000]:
                writer.writerow([
                    txn.date.isoformat(),
                    txn.description,
                    str(txn.amount),
                    txn.category.name if txn.category else "",
                    txn.account.name if txn.account else "",
                    txn.transaction_type,
                    ", ".join(t.name for t in txn.tags.all()),
                ])
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate(0)

        response = StreamingHttpResponse(generate_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        return response

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        """Bulk update transactions. Accepts {ids, category_id?, transaction_type?}."""
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"detail": "No transaction IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
        qs = Transaction.objects.filter(user=request.user, id__in=ids)
        updates = {}
        if "category_id" in request.data:
            cat_id = request.data["category_id"]
            if cat_id is not None and not Category.objects.filter(id=cat_id).exists():
                return Response({"detail": "Invalid category_id."}, status=status.HTTP_400_BAD_REQUEST)
            updates["category_id"] = cat_id
        if "transaction_type" in request.data:
            valid_types = {choice[0] for choice in Transaction.TRANSACTION_TYPES}
            if request.data["transaction_type"] not in valid_types:
                return Response(
                    {"detail": f"Invalid transaction_type. Must be one of: {', '.join(valid_types)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updates["transaction_type"] = request.data["transaction_type"]
        if not updates:
            return Response({"detail": "No fields to update."}, status=status.HTTP_400_BAD_REQUEST)
        count = qs.update(**updates)
        return Response({"updated": count})

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """Bulk delete transactions. Accepts {ids: []}."""
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"detail": "No transaction IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = Transaction.objects.filter(user=request.user, id__in=ids).delete()
        return Response({"deleted": count})

    @action(detail=False, methods=["get"])
    def duplicates(self, request):
        """Find potential duplicate transactions."""
        from transactions.dedup import find_potential_duplicates
        pairs = find_potential_duplicates(request.user)
        return Response({"duplicates": pairs, "count": len(pairs)})

    @action(detail=False, methods=["post"])
    def merge_duplicates(self, request):
        """Merge duplicate transactions. Keeps the first, deletes the second."""
        keep_id = request.data.get("keep_id")
        delete_id = request.data.get("delete_id")
        if not keep_id or not delete_id:
            return Response({"detail": "keep_id and delete_id required."}, status=status.HTTP_400_BAD_REQUEST)
        keep = Transaction.objects.filter(user=request.user, id=keep_id).first()
        delete = Transaction.objects.filter(user=request.user, id=delete_id).first()
        if not keep or not delete:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
        delete.delete()
        return Response({"kept": keep_id, "deleted": delete_id})

    @action(detail=False, methods=["post"], url_path="export/anonymized")
    def export_anonymized(self, request):
        """Export transactions as an anonymized CSV with PII stripped."""
        from django.http import HttpResponse

        from core.anonymize import export_anonymized_csv

        queryset = self.get_queryset()[:50000]
        csv_content = export_anonymized_csv(queryset)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions_anonymized.csv"'
        return response

    @action(detail=False, methods=["get"])
    def spending_summary(self, request):
        """Return spending grouped by category for a date range.

        Query params:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        """
        queryset = Transaction.objects.filter(
            user=request.user,
            transaction_type="expense",
        )

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        summary = (
            queryset
            .values("category__id", "category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        results = [
            {
                "category_id": entry["category__id"],
                "category_name": entry["category__name"] or "Uncategorized",
                "total": entry["total"],
            }
            for entry in summary
        ]

        return Response(results)


class GoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing financial goals."""

    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).select_related("category", "linked_account")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing budgets with spending progress."""

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Budget.objects.filter(user=self.request.user).select_related("category")
        active = self.request.query_params.get("active")
        if active and active.lower() == "true":
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def progress(self, request):
        """Return all active budgets with spending for current period."""
        from collections import defaultdict
        from datetime import timedelta
        from decimal import Decimal

        from django.utils import timezone

        budgets = list(Budget.objects.filter(user=request.user, is_active=True).select_related("category"))
        if not budgets:
            return Response([])

        # Pre-compute all spending in a single query to avoid N+1
        now = timezone.now()
        period_starts = {
            "weekly": (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).date(),
            "monthly": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date(),
            "annual": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).date(),
        }
        earliest = min(period_starts.values())

        expenses = Transaction.objects.filter(
            user=request.user, transaction_type="expense", date__gte=earliest
        ).values("category_id", "amount", "date")

        spending = defaultdict(Decimal)
        for exp in expenses:
            for period_name, period_start in period_starts.items():
                if exp["date"] >= period_start:
                    spending[(period_name, exp["category_id"])] += exp["amount"]
                    spending[(period_name, "__total__")] += exp["amount"]

        for b in budgets:
            if b.category_id:
                b._precomputed_spent = spending.get((b.period, b.category_id), Decimal("0"))
            else:
                b._precomputed_spent = spending.get((b.period, "__total__"), Decimal("0"))

        serializer = self.get_serializer(budgets, many=True)
        return Response(serializer.data)


class CategoryRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing auto-categorization rules."""

    serializer_class = CategoryRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CategoryRule.objects.filter(user=self.request.user).select_related("category")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing detected subscriptions."""

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Subscription.objects.filter(user=self.request.user).select_related("category")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="detect")
    def detect(self, request):
        """Run subscription detection on the user's transactions."""
        from transactions.subscriptions import detect_subscriptions
        detected = detect_subscriptions(request.user)
        return Response({"detected": len(detected), "subscriptions": detected})

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Return active subscriptions with next_expected in the next 30 days."""
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now().date()
        cutoff = now + timedelta(days=30)
        subs = Subscription.objects.filter(
            user=request.user, status="active",
            next_expected__gte=now, next_expected__lte=cutoff,
        ).select_related("category").order_by("next_expected")
        serializer = self.get_serializer(subs, many=True)
        return Response(serializer.data)
