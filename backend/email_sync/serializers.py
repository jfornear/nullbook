import re

from rest_framework import serializers

from .models import EmailAccount, EmailAttachment, EmailMessage, EmailRule


def _validate_regex(value, field_name):
    """Validate that a string is a valid regex pattern."""
    if not value:
        return value
    try:
        re.compile(value)
    except re.error as e:
        raise serializers.ValidationError(f"Invalid regex in {field_name}: {e}")
    return value


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = [
            "id",
            "provider",
            "email_address",
            "imap_host",
            "imap_port",
            "last_synced_at",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "last_synced_at",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]


class EmailRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailRule
        fields = [
            "id",
            "name",
            "is_active",
            "from_pattern",
            "subject_pattern",
            "has_attachment",
            "action",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_from_pattern(self, value):
        return _validate_regex(value, "from_pattern")

    def validate_subject_pattern(self, value):
        return _validate_regex(value, "subject_pattern")


class EmailAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = EmailAttachment
        fields = [
            "id",
            "filename",
            "content_type",
            "file_url",
            "receipt",
            "created_at",
        ]
        read_only_fields = ["id", "filename", "content_type", "file_url", "created_at"]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class EmailMessageSerializer(serializers.ModelSerializer):
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    email_address = serializers.CharField(source="email_account.email_address", read_only=True)

    class Meta:
        model = EmailMessage
        fields = [
            "id",
            "email_account",
            "email_address",
            "message_id",
            "from_address",
            "subject",
            "date",
            "matched_rule",
            "is_processed",
            "action_taken",
            "attachments",
            "created_at",
        ]
        read_only_fields = fields
