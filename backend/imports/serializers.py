from rest_framework import serializers

from .models import AmazonOrder, ImportBatch


class ImportBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportBatch
        fields = [
            "id",
            "account",
            "file_name",
            "status",
            "row_count",
            "imported_count",
            "error_log",
            "column_mapping",
            "bank_profile",
            "source_institution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "row_count",
            "imported_count",
            "error_log",
            "created_at",
            "updated_at",
        ]


class AmazonOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmazonOrder
        fields = [
            "id",
            "order_date",
            "order_id",
            "product_name",
            "asin",
            "total_amount",
            "quantity",
            "category",
            "matched_transaction",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UploadPreviewSerializer(serializers.Serializer):
    """Response serializer for the CSV upload/preview endpoint."""

    batch_id = serializers.IntegerField()
    file_name = serializers.CharField()
    headers = serializers.ListField(child=serializers.CharField())
    row_count = serializers.IntegerField()
    preview = serializers.ListField(child=serializers.DictField())
    detected_mapping = serializers.DictField(child=serializers.CharField())
    rows = serializers.ListField(child=serializers.DictField(), required=False)
    bank_profile = serializers.CharField(required=False, allow_null=True)
    bank_profile_name = serializers.CharField(required=False, allow_null=True)
    source_institution = serializers.CharField(required=False, allow_null=True)
