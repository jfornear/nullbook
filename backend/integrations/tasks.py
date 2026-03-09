import logging
from datetime import date
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_plaid_transactions(self, plaid_item_id):
    """Sync transactions for a single PlaidItem using cursor-based incremental sync.

    Steps:
        1. Load the PlaidItem and its sync cursors.
        2. Call Plaid transactions/sync with the stored cursor.
        3. For added transactions: find/create local Account, create Transaction.
        4. For modified transactions: update matching local Transaction.
        5. For removed transactions: mark local Transaction as deleted (soft-delete).
        6. Update sync cursor and account balances.
    """

    from .models import PlaidItem, PlaidSyncCursor
    from .plaid_client import sync_transactions

    try:
        plaid_item = PlaidItem.objects.get(id=plaid_item_id)
    except PlaidItem.DoesNotExist:
        logger.error("PlaidItem %s not found, skipping sync", plaid_item_id)
        return

    if plaid_item.status != "active":
        logger.info(
            "PlaidItem %s has status '%s', skipping sync",
            plaid_item_id,
            plaid_item.status,
        )
        return

    access_token = plaid_item.access_token
    user = plaid_item.user

    # Build a lookup of Plaid account_id -> PlaidSyncCursor
    cursors = {
        sc.account_id: sc
        for sc in PlaidSyncCursor.objects.filter(plaid_item=plaid_item).select_related("local_account")
    }

    # Use the first cursor value (they should be the same for item-level sync)
    current_cursor = ""
    for sc in cursors.values():
        if sc.cursor:
            current_cursor = sc.cursor
            break

    has_more = True
    total_added = 0
    total_modified = 0
    total_removed = 0

    try:
        while has_more:
            result = sync_transactions(access_token, cursor=current_cursor or None)

            # Update account balances from the response
            for plaid_account in result.get("accounts", []):
                account_id = getattr(plaid_account, "account_id", "")
                sc = cursors.get(account_id)
                if sc and sc.local_account:
                    balances = getattr(plaid_account, "balances", None)
                    if balances:
                        current_balance = getattr(balances, "current", None)
                        if current_balance is not None:
                            sc.local_account.balance = Decimal(str(current_balance))
                            sc.local_account.save(update_fields=["balance", "updated_at"])

            # Process added transactions
            for txn in result.get("added", []):
                _process_added_transaction(txn, user, plaid_item, cursors)
                total_added += 1

            # Process modified transactions
            for txn in result.get("modified", []):
                _process_modified_transaction(txn, user, cursors)
                total_modified += 1

            # Process removed transactions
            for txn in result.get("removed", []):
                _process_removed_transaction(txn, user)
                total_removed += 1

            current_cursor = result["next_cursor"]
            has_more = result["has_more"]

        # Update all cursors with the latest cursor value
        PlaidSyncCursor.objects.filter(plaid_item=plaid_item).update(
            cursor=current_cursor,
            updated_at=timezone.now(),
        )

        plaid_item.last_synced_at = timezone.now()
        plaid_item.error_code = ""
        plaid_item.error_message = ""
        plaid_item.save(update_fields=["last_synced_at", "error_code", "error_message", "updated_at"])

        logger.info(
            "PlaidItem %s synced: +%d ~%d -%d transactions",
            plaid_item_id,
            total_added,
            total_modified,
            total_removed,
        )

    except Exception as exc:
        logger.exception("Failed to sync PlaidItem %s", plaid_item_id)
        plaid_item.status = "error"
        plaid_item.error_code = getattr(exc, "code", "SYNC_ERROR")
        plaid_item.error_message = str(exc)[:1000]
        plaid_item.save(update_fields=["status", "error_code", "error_message", "updated_at"])
        raise self.retry(exc=exc)


def _process_added_transaction(plaid_txn, user, plaid_item, cursors):
    """Create a local Transaction from a Plaid added transaction."""
    from transactions.models import Category, Transaction

    from .mapping import map_plaid_category, normalize_merchant_name

    plaid_txn_id = getattr(plaid_txn, "transaction_id", "")
    account_id = getattr(plaid_txn, "account_id", "")

    # Find the local account via sync cursor
    sc = cursors.get(account_id)
    local_account = sc.local_account if sc else None

    if not local_account:
        logger.warning(
            "No local account for Plaid account %s, skipping transaction %s",
            account_id,
            plaid_txn_id,
        )
        return

    # Check for duplicate
    if Transaction.objects.filter(
        user=user,
        description__startswith=f"[plaid:{plaid_txn_id}]",
    ).exists():
        return

    # Determine amount and transaction type
    amount = Decimal(str(getattr(plaid_txn, "amount", 0)))
    # Plaid uses positive amounts for debits, negative for credits
    if amount > 0:
        transaction_type = "expense"
    elif amount < 0:
        transaction_type = "income"
        amount = abs(amount)
    else:
        transaction_type = "expense"

    # Check if it looks like a transfer
    pfc = getattr(plaid_txn, "personal_finance_category", None)
    if pfc:
        primary = getattr(pfc, "primary", "") if hasattr(pfc, "primary") else pfc.get("primary", "")
        if primary and primary.startswith("TRANSFER"):
            transaction_type = "transfer"

    # Map category
    category_name = "Uncategorized"
    if pfc:
        pfc_dict = {}
        if hasattr(pfc, "primary"):
            pfc_dict["primary"] = pfc.primary
            pfc_dict["detailed"] = getattr(pfc, "detailed", "")
        else:
            pfc_dict = pfc
        category_name = map_plaid_category(pfc_dict)

    category = Category.objects.filter(name=category_name).first()

    # Build description
    merchant = getattr(plaid_txn, "merchant_name", "") or getattr(plaid_txn, "name", "")
    description = normalize_merchant_name(merchant) or getattr(plaid_txn, "name", "Transaction")

    # Prepend plaid transaction ID for deduplication
    tagged_description = f"[plaid:{plaid_txn_id}] {description}"

    # Parse date
    txn_date = getattr(plaid_txn, "date", None) or date.today()
    if isinstance(txn_date, str):
        txn_date = date.fromisoformat(txn_date)

    Transaction.objects.create(
        user=user,
        account=local_account,
        category=category,
        date=txn_date,
        amount=amount,
        transaction_type=transaction_type,
        description=tagged_description,
    )


def _process_modified_transaction(plaid_txn, user, cursors):
    """Update an existing local Transaction from a Plaid modified transaction."""
    from transactions.models import Transaction

    from .mapping import normalize_merchant_name

    plaid_txn_id = getattr(plaid_txn, "transaction_id", "")

    try:
        local_txn = Transaction.objects.get(
            user=user,
            description__startswith=f"[plaid:{plaid_txn_id}]",
        )
    except Transaction.DoesNotExist:
        # If we don't have it locally, treat as an add
        logger.info("Modified transaction %s not found locally, skipping", plaid_txn_id)
        return

    # Update amount
    amount = Decimal(str(getattr(plaid_txn, "amount", 0)))
    if amount > 0:
        local_txn.transaction_type = "expense"
        local_txn.amount = amount
    elif amount < 0:
        local_txn.transaction_type = "income"
        local_txn.amount = abs(amount)

    # Update date
    txn_date = getattr(plaid_txn, "date", None)
    if txn_date:
        if isinstance(txn_date, str):
            txn_date = date.fromisoformat(txn_date)
        local_txn.date = txn_date

    # Update description
    merchant = getattr(plaid_txn, "merchant_name", "") or getattr(plaid_txn, "name", "")
    cleaned = normalize_merchant_name(merchant) or getattr(plaid_txn, "name", "Transaction")
    local_txn.description = f"[plaid:{plaid_txn_id}] {cleaned}"

    local_txn.save()


def _process_removed_transaction(plaid_txn, user):
    """Delete a local Transaction that was removed from Plaid."""
    from transactions.models import Transaction

    plaid_txn_id = getattr(plaid_txn, "transaction_id", "")

    Transaction.objects.filter(
        user=user,
        description__startswith=f"[plaid:{plaid_txn_id}]",
    ).delete()


@shared_task
def sync_all_plaid_items():
    """Scheduled task to sync all active PlaidItems.

    Intended to run on a periodic schedule (e.g., every 4-6 hours)
    via Celery Beat.
    """
    from .models import PlaidItem

    active_items = PlaidItem.objects.filter(status="active")
    count = 0

    for item in active_items:
        sync_plaid_transactions.delay(item.id)
        count += 1

    logger.info("Queued sync for %d active PlaidItems", count)
    return count
