from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeductibleExpense, Receipt, TaxDocument, TaxYear
from .serializers import (
    DeductibleExpenseSerializer,
    ReceiptSerializer,
    TaxDocumentSerializer,
    TaxYearSerializer,
)
from .tasks import process_receipt_task


class TaxYearViewSet(viewsets.ModelViewSet):
    serializer_class = TaxYearSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaxYear.objects.filter(user=self.request.user).prefetch_related("documents", "deductions")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def estimate(self, request, pk=None):
        """Calculate tax estimate for this tax year."""
        tax_year = self.get_object()
        from .export import generate_tax_summary
        summary = generate_tax_summary(request.user, tax_year.year)
        return Response(summary)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """Export tax summary as CSV."""
        tax_year = self.get_object()
        from .export import export_tax_csv
        csv_content = export_tax_csv(request.user, tax_year.year)
        if not csv_content:
            return Response({"detail": "No data to export."}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="tax_summary_{tax_year.year}.csv"'
        return response

    @action(detail=True, methods=["get"], url_path="expense-report")
    def expense_report(self, request, pk=None):
        """Generate expense report for a tax year.

        Query params:
            format: "json" (default), "csv", or "text"
        """
        tax_year = self.get_object()
        fmt = request.query_params.get("format", "json")

        from .expense_report import generate_expense_report
        report = generate_expense_report(request.user, tax_year.year, fmt=fmt)

        if fmt == "csv":
            response = HttpResponse(report, content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="expense_report_{tax_year.year}.csv"'
            )
            return response
        elif fmt == "text":
            response = HttpResponse(report, content_type="text/plain")
            response["Content-Disposition"] = (
                f'attachment; filename="expense_report_{tax_year.year}.txt"'
            )
            return response
        else:
            return Response(report)


class TaxDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TaxDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaxDocument.objects.filter(tax_year__user=self.request.user)


class DeductibleExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = DeductibleExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeductibleExpense.objects.filter(tax_year__user=self.request.user)


class ReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Receipt.objects.filter(user=self.request.user).prefetch_related("line_items")

    def perform_create(self, serializer):
        receipt = serializer.save(user=self.request.user)
        process_receipt_task.delay(receipt.id)

    @action(detail=True, methods=["post"])
    def create_expense(self, request, pk=None):
        """Create a DeductibleExpense from a processed receipt's OCR data."""
        receipt = self.get_object()
        if receipt.status != "completed":
            return Response(
                {"detail": "Receipt has not been processed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tax_year_id = request.data.get("tax_year_id")
        deduction_type = request.data.get("deduction_type", "business")

        try:
            tax_year = TaxYear.objects.get(id=tax_year_id, user=request.user)
        except TaxYear.DoesNotExist:
            return Response(
                {"detail": "Tax year not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        expense = DeductibleExpense.objects.create(
            tax_year=tax_year,
            receipt=receipt,
            deduction_type=deduction_type,
            description=f"{receipt.merchant} - {receipt.date or 'no date'}",
            amount=receipt.total_amount or 0,
        )
        receipt.deductible_expense = expense
        receipt.tax_year = tax_year
        receipt.save(update_fields=["deductible_expense", "tax_year"])

        return Response(
            DeductibleExpenseSerializer(expense).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        """Re-run OCR on a receipt."""
        receipt = self.get_object()
        receipt.status = "pending"
        receipt.error_message = ""
        receipt.save(update_fields=["status", "error_message"])
        process_receipt_task.delay(receipt.id)
        return Response({"detail": "Reprocessing started."})
