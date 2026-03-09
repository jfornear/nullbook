from rest_framework import serializers

from .models import Account, BalanceHistory, Institution


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            "id",
            "name",
            "institution_type",
            "website",
            "logo_url",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AccountSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_logo_url = serializers.URLField(source="institution.logo_url", read_only=True, default="")

    class Meta:
        model = Account
        fields = [
            "id",
            "institution",
            "institution_name",
            "institution_logo_url",
            "name",
            "account_type",
            "balance",
            "currency",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceHistory
        fields = [
            "id",
            "account",
            "date",
            "balance",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
