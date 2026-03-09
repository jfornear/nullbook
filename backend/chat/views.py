from django.db.models import Case, Count, IntegerField, Value, When
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Conversation
from .serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
)


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationSerializer

    def get_queryset(self):
        return (
            Conversation.objects.filter(user=self.request.user, is_archived=False)
            .annotate(
                message_count=Count("messages"),
                pin_order=Case(
                    When(is_pinned=True, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
            )
            .order_by("pin_order", "-updated_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
