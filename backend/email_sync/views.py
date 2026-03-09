import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EmailAccount, EmailMessage, EmailRule
from .serializers import EmailAccountSerializer, EmailMessageSerializer, EmailRuleSerializer
from .tasks import scan_single_email_account

logger = logging.getLogger(__name__)


class EmailAccountViewSet(viewsets.ModelViewSet):
    serializer_class = EmailAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmailAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="connect-imap")
    def connect_imap(self, request):
        """Test and save an IMAP connection."""
        from .imap_client import connect_imap

        email_address = request.data.get("email_address")
        imap_host = request.data.get("imap_host")
        imap_port = request.data.get("imap_port", 993)
        username = request.data.get("username")
        password = request.data.get("password")

        if not all([email_address, imap_host, username, password]):
            return Response(
                {"detail": "email_address, imap_host, username, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a temporary account to test the connection
        email_account, created = EmailAccount.objects.get_or_create(
            user=request.user,
            email_address=email_address,
            defaults={
                "provider": "imap",
                "imap_host": imap_host,
                "imap_port": imap_port,
            },
        )
        email_account.credentials = {"username": username, "password": password}
        email_account.imap_host = imap_host
        email_account.imap_port = imap_port
        email_account.provider = "imap"

        # Test the connection
        try:
            conn = connect_imap(email_account)
            conn.logout()
        except Exception:
            logger.exception("IMAP connection failed for %s", email_address)
            # If we just created it, delete the failed account
            if created:
                email_account.delete()
            return Response(
                {"detail": "IMAP connection failed. Check your credentials and server settings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_account.status = "active"
        email_account.error_message = ""
        email_account.save()

        return Response(
            EmailAccountSerializer(email_account).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="sync-now")
    def sync_now(self, request, pk=None):
        """Trigger a manual scan of this email account."""
        email_account = self.get_object()

        if email_account.status == "disconnected":
            return Response(
                {"detail": "Email account is disconnected. Reconnect first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scan_single_email_account.delay(email_account.id)
        return Response({"detail": "Sync started."})


class EmailRuleViewSet(viewsets.ModelViewSet):
    serializer_class = EmailRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmailRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmailMessageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = EmailMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            EmailMessage.objects.filter(email_account__user=self.request.user)
            .select_related("email_account", "matched_rule")
            .prefetch_related("attachments")
        )
