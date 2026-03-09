import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PlaidItem, PlaidSyncCursor
from .plaid_client import create_link_token, exchange_public_token, get_accounts
from .serializers import LinkTokenSerializer, PlaidItemSerializer
from .mapping import map_plaid_account_type
from .tasks import sync_plaid_transactions

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_link_token_view(request):
    """Create a Plaid Link token for the authenticated user.

    POST /api/integrations/plaid/link-token/

    Returns:
        link_token, expiration, request_id
    """
    try:
        result = create_link_token(request.user)
        serializer = LinkTokenSerializer(result)
        return Response(serializer.data)
    except Exception:
        logger.exception("Failed to create Plaid link token")
        return Response(
            {"error": "Failed to create link token. Please try again."},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def exchange_token_view(request):
    """Exchange a Plaid public token for an access token and create a PlaidItem.

    POST /api/integrations/plaid/exchange/

    Expects:
        public_token: str
        institution_id: str (optional)
        institution_name: str (optional)

    Returns:
        PlaidItem data and synced accounts.
    """
    public_token = request.data.get("public_token")
    if not public_token:
        return Response(
            {"error": "public_token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    institution_id = request.data.get("institution_id", "")
    institution_name = request.data.get("institution_name", "")

    try:
        # Exchange the public token
        exchange_result = exchange_public_token(public_token)

        # Check if this item already exists
        existing = PlaidItem.objects.filter(
            item_id=exchange_result["item_id"]
        ).first()
        if existing:
            serializer = PlaidItemSerializer(existing)
            return Response(
                {"item": serializer.data, "already_connected": True},
                status=status.HTTP_200_OK,
            )

        # Find or create a local Institution record
        local_institution = None
        if institution_name:
            from accounts.models import Institution

            local_institution, _ = Institution.objects.get_or_create(
                name=institution_name,
                defaults={"institution_type": "bank"},
            )

        # Create the PlaidItem
        plaid_item = PlaidItem(
            user=request.user,
            item_id=exchange_result["item_id"],
            plaid_institution_id=institution_id,
            institution_name=institution_name,
            institution=local_institution,
        )
        plaid_item.access_token = exchange_result["access_token"]
        plaid_item.save()

        # Fetch and sync accounts from Plaid
        accounts_result = get_accounts(plaid_item.access_token)
        synced_accounts = _sync_plaid_accounts(
            request.user, plaid_item, accounts_result["accounts"]
        )

        # Kick off initial transaction sync
        sync_plaid_transactions.delay(plaid_item.id)

        serializer = PlaidItemSerializer(plaid_item)
        return Response(
            {
                "item": serializer.data,
                "accounts_synced": len(synced_accounts),
                "already_connected": False,
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception:
        logger.exception("Failed to exchange Plaid token")
        return Response(
            {"error": "Failed to connect account. Please try again."},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_item_view(request):
    """Trigger a manual transaction sync for a PlaidItem.

    POST /api/integrations/plaid/sync/

    Expects:
        plaid_item_id: int
    """
    plaid_item_id = request.data.get("plaid_item_id")
    if not plaid_item_id:
        return Response(
            {"error": "plaid_item_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        plaid_item = PlaidItem.objects.get(
            id=plaid_item_id,
            user=request.user,
        )
    except PlaidItem.DoesNotExist:
        return Response(
            {"error": "Plaid item not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if plaid_item.status != "active":
        return Response(
            {"error": f"Cannot sync item with status '{plaid_item.status}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sync_plaid_transactions.delay(plaid_item.id)

    return Response({"status": "sync_started", "plaid_item_id": plaid_item.id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_plaid_items_view(request):
    """List all Plaid items for the authenticated user.

    GET /api/integrations/plaid/items/
    """
    items = PlaidItem.objects.filter(user=request.user)
    serializer = PlaidItemSerializer(items, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_plaid_item_view(request, pk):
    """Disconnect a Plaid item.

    DELETE /api/integrations/plaid/items/<pk>/

    This removes the PlaidItem and its sync cursors. Linked accounts
    and transactions are preserved but no longer sync.
    """
    try:
        plaid_item = PlaidItem.objects.get(id=pk, user=request.user)
    except PlaidItem.DoesNotExist:
        return Response(
            {"error": "Plaid item not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    institution_name = plaid_item.institution_name
    plaid_item.delete()

    return Response(
        {"status": "disconnected", "institution_name": institution_name},
        status=status.HTTP_200_OK,
    )


def _sync_plaid_accounts(user, plaid_item, plaid_accounts):
    """Create or update local Account records from Plaid accounts.

    Args:
        user: Django User instance.
        plaid_item: PlaidItem instance.
        plaid_accounts: List of Plaid account objects.

    Returns:
        List of local Account instances that were created/updated.
    """
    from accounts.models import Account

    synced = []
    for pa in plaid_accounts:
        account_type = map_plaid_account_type(
            getattr(pa, "type", "other"),
            getattr(pa, "subtype", None),
        )
        balance = 0
        balances = getattr(pa, "balances", None)
        if balances:
            balance = getattr(balances, "current", 0) or 0

        account_name = getattr(pa, "official_name", "") or getattr(pa, "name", "Account")
        currency = "USD"
        if balances:
            currency = getattr(balances, "iso_currency_code", "USD") or "USD"

        # Find existing or create new local account
        account, created = Account.objects.get_or_create(
            user=user,
            name=account_name,
            institution=plaid_item.institution,
            defaults={
                "account_type": account_type,
                "balance": balance,
                "currency": currency,
            },
        )

        if not created:
            account.balance = balance
            account.save(update_fields=["balance", "updated_at"])

        # Create or update the sync cursor for this account
        PlaidSyncCursor.objects.update_or_create(
            plaid_item=plaid_item,
            account_id=getattr(pa, "account_id", ""),
            defaults={"local_account": account},
        )

        synced.append(account)

    return synced
