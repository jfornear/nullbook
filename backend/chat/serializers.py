from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "role",
            "content",
            "tool_calls",
            "tool_results",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "is_pinned",
            "is_archived",
            "message_count",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return {
                "role": msg.role,
                "content": msg.content[:100],
                "created_at": msg.created_at.isoformat(),
            }
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "is_pinned",
            "is_archived",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
