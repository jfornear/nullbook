from rest_framework import serializers

from .models import ImportBatch


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


class UploadPreviewSerializer(serializers.Serializer):
    """Response serializer for the CSV upload/preview endpoint."""

    batch_id = serializers.IntegerField()
    file_name = serializers.CharField()
    headers = serializers.ListField(child=serializers.CharField())
    row_count = serializers.IntegerField()
    preview = serializers.ListField(child=serializers.DictField())
    detected_mapping = serializers.DictField(child=serializers.CharField())
    rows = serializers.ListField(child=serializers.DictField(), required=False)
