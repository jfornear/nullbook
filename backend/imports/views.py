from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transactions.models import Transaction

from .models import ImportBatch
from .parsers import apply_mapping, parse_file
from .serializers import ImportBatchSerializer, UploadPreviewSerializer


class ImportBatchViewSet(viewsets.ModelViewSet):
    """ViewSet for managing CSV import batches."""

    serializer_class = ImportBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_id:
            return Response(
                {"error": "Account ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the account belongs to the user
        from accounts.models import Account

        try:
            account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            file_content = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"error": "File must be a valid UTF-8 encoded file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed = parse_file(file_content, csv_file.name)

        if not parsed["headers"]:
            return Response(
                {"error": "CSV file appears to be empty or has no headers."},
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
        )

        response_data = {
            "batch_id": batch.id,
            "file_name": batch.file_name,
            "headers": parsed["headers"],
            "row_count": parsed["row_count"],
            "preview": parsed["preview"],
            "detected_mapping": parsed["detected_mapping"],
            "rows": parsed["rows"],
        }

        serializer = UploadPreviewSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
                {"error": "This batch has already been imported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mapping = request.data.get("mapping", batch.column_mapping)
        rows = request.data.get("rows")

        if not rows:
            return Response(
                {"error": "No rows provided for import."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not mapping or not mapping.get("date") or not mapping.get("amount"):
            return Response(
                {"error": "Column mapping must include at least 'date' and 'amount'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update mapping if the client sent an override
        if request.data.get("mapping"):
            batch.column_mapping = mapping
            batch.save(update_fields=["column_mapping", "updated_at"])

        result = apply_mapping(rows, mapping)

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
