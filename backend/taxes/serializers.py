from rest_framework import serializers

from .models import DeductibleExpense, Receipt, ReceiptLineItem, TaxDocument, TaxYear


class _TaxYearOwnershipMixin:
    """Validate that tax_year belongs to the requesting user."""

    def validate_tax_year(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid tax year.")
        return value


class DeductibleExpenseSerializer(_TaxYearOwnershipMixin, serializers.ModelSerializer):
    class Meta:
        model = DeductibleExpense
        fields = [
            "id",
            "tax_year",
            "receipt",
            "deduction_type",
            "description",
            "amount",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TaxDocumentSerializer(_TaxYearOwnershipMixin, serializers.ModelSerializer):
    class Meta:
        model = TaxDocument
        fields = [
            "id",
            "tax_year",
            "document_type",
            "issuer",
            "amount",
            "details",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TaxYearSerializer(serializers.ModelSerializer):
    documents = TaxDocumentSerializer(many=True, read_only=True)
    deductions = DeductibleExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = TaxYear
        fields = [
            "id",
            "year",
            "filing_status",
            "federal_tax_paid",
            "state_tax_paid",
            "notes",
            "documents",
            "deductions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_year(self, value):
        request = self.context.get("request")
        if request:
            qs = TaxYear.objects.filter(user=request.user, year=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"You already have a tax year for {value}."
                )
        return value


class ReceiptLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptLineItem
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "total_price",
            "category",
        ]
        read_only_fields = ["id"]


class ReceiptSerializer(serializers.ModelSerializer):
    line_items = ReceiptLineItemSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    def validate_transaction(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid transaction.")
        return value

    def validate_tax_year(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid tax year.")
        return value

    class Meta:
        model = Receipt
        fields = [
            "id",
            "image",
            "image_url",
            "status",
            "merchant",
            "date",
            "total_amount",
            "subtotal",
            "tax_amount",
            "tip_amount",
            "currency",
            "payment_method",
            "category",
            "transaction",
            "deductible_expense",
            "tax_year",
            "error_message",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
