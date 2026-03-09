from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Account, BalanceHistory, Institution
from .serializers import AccountSerializer, BalanceHistorySerializer, InstitutionSerializer


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for institutions (shared lookup data)."""

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Account.objects.filter(user=self.request.user)

        account_type = self.request.query_params.get("account_type")
        if account_type:
            queryset = queryset.filter(account_type=account_type)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BalanceHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = BalanceHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BalanceHistory.objects.filter(account__user=self.request.user)

    def perform_create(self, serializer):
        account = serializer.validated_data.get("account")
        if account and account.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot add balance history to another user's account.")
        serializer.save()
