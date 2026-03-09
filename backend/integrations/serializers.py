from rest_framework import serializers

from .models import PlaidItem


class PlaidItemSerializer(serializers.ModelSerializer):
    """Read-only serializer for PlaidItem. Excludes access_token."""

    class Meta:
        model = PlaidItem
        fields = [
            "id",
            "item_id",
            "plaid_institution_id",
            "institution_name",
            "institution",
            "status",
            "error_code",
            "error_message",
            "consent_expires_at",
            "last_synced_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LinkTokenSerializer(serializers.Serializer):
    """Serializer for Plaid Link token response."""

    link_token = serializers.CharField()
    expiration = serializers.CharField()
    request_id = serializers.CharField()
