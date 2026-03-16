from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transactions.models import Transaction

from .models import AmazonOrder, ImportBatch
from .parsers import apply_mapping, list_bank_profiles, parse_file
from .serializers import AmazonOrderSerializer, ImportBatchSerializer, UploadPreviewSerializer


class ImportBatchViewSet(viewsets.ModelViewSet):
    """ViewSet for managing CSV import batches."""

    serializer_class = ImportBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload a CSV file, parse it, and return a preview.

        Expects:
            - file: CSV file upload
            - account: Account ID to import into
        """
        csv_file = request.FILES.get("file")
        account_id = request.data.get("account")

        if not csv_file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_id:
            return Response(
                {"detail": "Account ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the account belongs to the user
        from accounts.models import Account

        try:
            account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response(
                {"detail": "Account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if csv_file.size > self.MAX_UPLOAD_SIZE:
            return Response(
                {"detail": "File too large. Maximum size is 50 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_content = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "File must be a valid UTF-8 encoded file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed = parse_file(file_content, csv_file.name)

        if not parsed["headers"]:
            return Response(
                {"detail": "CSV file appears to be empty or has no headers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the batch in preview status
        batch = ImportBatch.objects.create(
            user=request.user,
            account=account,
            file_name=csv_file.name,
            status="preview",
            row_count=parsed["row_count"],
            column_mapping=parsed["detected_mapping"],
            bank_profile=parsed.get("bank_profile") or "",
            source_institution=parsed.get("source_institution") or "",
        )

        response_data = {
            "batch_id": batch.id,
            "file_name": batch.file_name,
            "headers": parsed["headers"],
            "row_count": parsed["row_count"],
            "preview": parsed["preview"],
            "detected_mapping": parsed["detected_mapping"],
            "rows": parsed["rows"],
            "bank_profile": parsed.get("bank_profile"),
            "bank_profile_name": parsed.get("bank_profile_name"),
            "source_institution": parsed.get("source_institution"),
        }

        serializer = UploadPreviewSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="bank-profiles")
    def bank_profiles(self, request):
        """List all supported bank import profiles."""
        return Response(list_bank_profiles())

    @action(detail=True, methods=["post"], url_path="execute")
    def execute(self, request, pk=None):
        """Execute the import: create Transaction objects from the batch.

        Expects:
            - mapping (optional): Column mapping override, e.g.
              {"date": "Date", "amount": "Amount", "description": "Description"}
            - rows: The raw CSV rows (list of dicts) to import.
              If not provided, the client must re-upload or we reject.
        """
        batch = self.get_object()

        if batch.status == "completed":
            return Response(
                {"detail": "This batch has already been imported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mapping = request.data.get("mapping", batch.column_mapping)
        rows = request.data.get("rows")

        if not rows:
            return Response(
                {"detail": "No rows provided for import."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not mapping or not mapping.get("date") or not mapping.get("amount"):
            return Response(
                {"detail": "Column mapping must include at least 'date' and 'amount'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update mapping if the client sent an override
        if request.data.get("mapping"):
            batch.column_mapping = mapping
            batch.save(update_fields=["column_mapping", "updated_at"])

        result = apply_mapping(rows, mapping, bank_profile_id=batch.bank_profile)

        # Build lookup set for duplicate detection
        existing = set(
            Transaction.objects.filter(
                user=request.user,
                account=batch.account,
            ).values_list("date", "amount", "description")
        )

        transactions_to_create = []
        duplicates_skipped = 0
        for txn_data in result["transactions"]:
            key = (txn_data["date"], Decimal(txn_data["amount"]), txn_data["description"])
            if key in existing:
                duplicates_skipped += 1
                continue
            existing.add(key)
            transactions_to_create.append(
                Transaction(
                    user=request.user,
                    account=batch.account,
                    date=txn_data["date"],
                    amount=Decimal(txn_data["amount"]),
                    transaction_type=txn_data["transaction_type"],
                    description=txn_data["description"],
                    import_batch=batch,
                )
            )

        created = Transaction.objects.bulk_create(transactions_to_create)
        if duplicates_skipped:
            result["errors"].append(f"{duplicates_skipped} duplicate transaction(s) skipped.")

        batch.status = "completed"
        batch.imported_count = len(created)
        batch.error_log = "\n".join(result["errors"]) if result["errors"] else ""
        batch.save(update_fields=["status", "imported_count", "error_log", "updated_at"])

        return Response({
            "batch_id": batch.id,
            "status": batch.status,
            "imported_count": batch.imported_count,
            "error_count": len(result["errors"]),
            "errors": result["errors"],
        })


class AmazonOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Amazon order cross-referencing."""

    serializer_class = AmazonOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AmazonOrder.objects.filter(user=self.request.user)

    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload an Amazon Order History CSV and parse it."""
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if csv_file.size > self.MAX_UPLOAD_SIZE:
            return Response(
                {"detail": "File too large. Maximum size is 50 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_content = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "File must be a valid UTF-8 encoded file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .parsers.amazon_parser import parse_amazon_orders

        parsed = parse_amazon_orders(file_content)

        # Filter by year if provided
        year = request.data.get("year")

        # Create AmazonOrder records
        created_count = 0
        for order in parsed["orders"]:
            if year and not order["order_date"].startswith(str(year)):
                continue

            AmazonOrder.objects.update_or_create(
                user=request.user,
                order_id=order["order_id"],
                product_name=order["product_name"][:500],
                defaults={
                    "order_date": order["order_date"],
                    "asin": order.get("asin", ""),
                    "total_amount": Decimal(order["total_amount"]),
                    "quantity": order.get("quantity", 1),
                    "category": order.get("category", ""),
                },
            )
            created_count += 1

        return Response({
            "orders_parsed": parsed["order_count"],
            "orders_saved": created_count,
            "date_range": parsed["date_range"],
            "errors": parsed.get("errors", []),
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="matches")
    def matches(self, request):
        """Find matches between Amazon orders and bank transactions."""
        from .amazon_matcher import match_amazon_orders

        orders = list(self.get_queryset().values(
            "order_date", "order_id", "product_name", "total_amount"
        ))
        # Convert to the format expected by the matcher
        order_dicts = [
            {
                "order_date": str(o["order_date"]),
                "order_id": o["order_id"],
                "product_name": o["product_name"],
                "total_amount": str(o["total_amount"]),
            }
            for o in orders
        ]

        matches = match_amazon_orders(request.user, order_dicts)
        return Response({
            "matches": matches,
            "match_count": len(matches),
            "total_orders": len(order_dicts),
        })

    @action(detail=False, methods=["post"], url_path="apply")
    def apply_matches(self, request):
        """Apply matched Amazon orders to transactions (update notes with product names)."""
        from .amazon_matcher import apply_matches as do_apply

        matches = request.data.get("matches", [])
        if not matches:
            return Response(
                {"detail": "No matches provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = do_apply(request.user, matches)

        # Update matched_transaction FK on AmazonOrder records
        # Only link to transactions that belong to this user
        user_txn_ids = set(
            Transaction.objects.filter(
                user=request.user,
                id__in=[m.get("transaction_id") for m in matches if m.get("transaction_id")],
            ).values_list("id", flat=True)
        )
        for match in matches:
            txn_id = match.get("transaction_id")
            order_id = match.get("order", {}).get("order_id")
            if txn_id and order_id and txn_id in user_txn_ids:
                AmazonOrder.objects.filter(
                    user=request.user,
                    order_id=order_id,
                ).update(matched_transaction_id=txn_id)

        return Response(result)
