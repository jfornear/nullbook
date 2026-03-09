from rest_framework import serializers

from .models import Alert, UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["id", "currency", "fiscal_year_start", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id", "alert_type", "severity", "title", "message",
            "is_read", "action_url", "metadata", "created_at",
        ]
        read_only_fields = ["created_at"]
