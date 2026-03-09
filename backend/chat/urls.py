from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .streaming import stream_chat
from .views import ConversationViewSet

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path(
        "conversations/<uuid:conversation_id>/stream/",
        stream_chat,
        name="conversation-stream",
    ),
    path("", include(router.urls)),
]
