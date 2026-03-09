"""Receipt-to-transaction matching engine.

Automatically matches processed receipts to existing transactions
based on amount, date, and merchant name similarity.
"""

import logging
from datetime import timedelta


logger = logging.getLogger(__name__)


def match_receipt_to_transaction(receipt) -> dict | None:
    """Attempt to match a receipt to an existing transaction.

    Matching criteria (in order of priority):
    1. Exact amount + date within 3 days + merchant name similarity
    2. Exact amount + date within 7 days
    3. Close amount (within 5%) + date within 3 days + merchant match

    Returns matched transaction info or None.
    """
    from transactions.models import Transaction

    if not receipt.total_amount or not receipt.date:
        return None

    user = receipt.user
    amount = receipt.total_amount
    date = receipt.date
    merchant = (receipt.merchant or "").lower()

    # Search window
    date_start = date - timedelta(days=3)
    date_end = date + timedelta(days=3)

    candidates = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__gte=date_start,
        date__lte=date_end,
    ).exclude(receipts__isnull=False)  # Exclude already-matched

    # Priority 1: Exact amount + merchant match
    for txn in candidates.filter(amount=amount):
        if merchant and _merchant_similarity(merchant, txn.description.lower()) > 0.5:
            return _link_receipt(receipt, txn, "exact_amount_merchant")

    # Priority 2: Exact amount within 7-day window
    wide_candidates = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        amount=amount,
        date__gte=date - timedelta(days=7),
        date__lte=date + timedelta(days=7),
    ).exclude(receipts__isnull=False)

    if wide_candidates.count() == 1:
        return _link_receipt(receipt, wide_candidates.first(), "exact_amount_date")

    # Priority 3: Close amount + merchant match
    tolerance = amount * 5 / 100  # 5% tolerance
    close_candidates = candidates.filter(
        amount__gte=amount - tolerance,
        amount__lte=amount + tolerance,
    )
    for txn in close_candidates:
        if merchant and _merchant_similarity(merchant, txn.description.lower()) > 0.5:
            return _link_receipt(receipt, txn, "close_amount_merchant")

    return None


def _merchant_similarity(merchant: str, description: str) -> float:
    """Simple token-based similarity between merchant name and description."""
    merchant_tokens = set(merchant.lower().split())
    desc_tokens = set(description.lower().split())

    if not merchant_tokens:
        return 0

    # Check if any merchant token appears in description
    overlap = merchant_tokens & desc_tokens
    return len(overlap) / len(merchant_tokens)


def _link_receipt(receipt, transaction, match_type: str) -> dict:
    """Link a receipt to a transaction."""
    receipt.transaction = transaction
    receipt.save(update_fields=["transaction", "updated_at"])

    logger.info(
        "Matched receipt %d to transaction %d (%s)",
        receipt.id,
        transaction.id,
        match_type,
    )

    return {
        "receipt_id": receipt.id,
        "transaction_id": transaction.id,
        "match_type": match_type,
        "merchant": receipt.merchant,
        "amount": str(receipt.total_amount),
        "date": str(receipt.date),
    }


def auto_link_tax_year(receipt):
    """Auto-link a receipt to the appropriate tax year based on date."""
    from taxes.models import TaxYear

    if not receipt.date or receipt.tax_year:
        return

    year = receipt.date.year
    tax_year = TaxYear.objects.filter(user=receipt.user, year=year).first()
    if tax_year:
        receipt.tax_year = tax_year
        receipt.save(update_fields=["tax_year", "updated_at"])


def batch_match_receipts(user) -> dict:
    """Match all unmatched completed receipts to transactions."""
    from taxes.models import Receipt

    receipts = list(Receipt.objects.filter(
        user=user,
        status="completed",
        transaction__isnull=True,
    ))

    matched = 0
    for receipt in receipts:
        result = match_receipt_to_transaction(receipt)
        if result:
            matched += 1
        auto_link_tax_year(receipt)

    return {"matched": matched, "total": len(receipts)}
