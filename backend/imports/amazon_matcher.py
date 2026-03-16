"""Amazon order to bank transaction matcher.

Matches Amazon orders (from the "Request My Data" export) to bank
transactions with "AMAZON" / "AMZN" in the description, using date
proximity and amount matching.
"""

from datetime import date as date_type
from decimal import Decimal

from django.db.models import Q

from transactions.models import Transaction


def match_amazon_orders(user, amazon_orders: list[dict], date_tolerance: int = 3,
                        amount_tolerance: Decimal = Decimal("0.50")) -> list[dict]:
    """Match Amazon orders to bank transactions.

    Args:
        user: Django user instance.
        amazon_orders: List of parsed Amazon order dicts with
            order_date, product_name, total_amount.
        date_tolerance: Number of days to allow between order and charge.
        amount_tolerance: Dollar amount difference to allow.

    Returns:
        List of match dicts with: order, transaction, confidence.
    """
    # Find all Amazon-like transactions using case-insensitive contains
    amazon_txns = list(
        Transaction.objects.filter(
            user=user,
            transaction_type="expense",
        ).filter(
            Q(description__icontains="AMAZON")
            | Q(description__icontains="AMZN")
            | Q(description__icontains="AMZ*")
        ).order_by("date")
    )

    if not amazon_txns:
        return []

    matches = []
    matched_txn_ids = set()
    matched_order_ids = set()

    for order in amazon_orders:
        order_date = date_type.fromisoformat(order["order_date"])
        order_amount = Decimal(order["total_amount"])

        if order_amount <= 0:
            continue

        best_match = None
        best_score = float("inf")

        for txn in amazon_txns:
            if txn.id in matched_txn_ids:
                continue

            # Date proximity
            date_diff = abs((txn.date - order_date).days)
            if date_diff > date_tolerance:
                continue

            # Amount proximity
            amount_diff = abs(txn.amount - order_amount)
            if amount_diff > amount_tolerance:
                continue

            # Score: lower is better (prefer exact matches)
            score = date_diff + float(amount_diff)
            if score < best_score:
                best_score = score
                best_match = txn

        if best_match:
            order_key = f"{order['order_id']}_{order['product_name']}"
            if order_key in matched_order_ids:
                continue

            confidence = "high" if best_score < 1.0 else "medium"
            matches.append({
                "order": order,
                "transaction_id": best_match.id,
                "transaction_date": str(best_match.date),
                "transaction_description": best_match.description,
                "transaction_amount": str(best_match.amount),
                "date_diff_days": abs((best_match.date - order_date).days),
                "amount_diff": str(abs(best_match.amount - order_amount)),
                "confidence": confidence,
            })
            matched_txn_ids.add(best_match.id)
            matched_order_ids.add(order_key)

    return matches


def apply_matches(user, matches: list[dict]) -> dict:
    """Apply matched Amazon orders to transactions.

    Updates the transaction notes field with the product name.

    Args:
        user: Django user instance.
        matches: List of match dicts from match_amazon_orders().

    Returns:
        dict with applied count.
    """
    applied = 0

    for match in matches:
        txn_id = match.get("transaction_id")
        product_name = match.get("order", {}).get("product_name", "")

        if not txn_id or not product_name:
            continue

        try:
            txn = Transaction.objects.get(id=txn_id, user=user)
            # Append product name to notes
            existing_notes = txn.notes or ""
            if product_name not in existing_notes:
                separator = "\n" if existing_notes else ""
                txn.notes = f"{existing_notes}{separator}Amazon: {product_name}"
                txn.save(update_fields=["notes", "updated_at"])
                applied += 1
        except Transaction.DoesNotExist:
            continue

    return {"applied": applied, "total": len(matches)}


def suggest_business_category(product_name: str) -> str | None:
    """Suggest whether an Amazon purchase is business or personal based on keywords."""
    name = product_name.upper()

    business_keywords = [
        "LAPTOP", "MONITOR", "KEYBOARD", "MOUSE", "WEBCAM", "MICROPHONE",
        "HEADSET", "HEADPHONE", "CABLE", "ADAPTER", "CHARGER", "DOCK",
        "USB", "HDMI", "TRIPOD", "CAMERA", "SD CARD", "SSD", "HARD DRIVE",
        "POWER BANK", "SURGE PROTECTOR", "DESK", "CHAIR", "STAND",
        "BACKPACK", "CASE", "SLEEVE", "ORGANIZER", "WHITEBOARD",
        "NOTEBOOK", "PEN ", "MARKER", "LABEL", "PRINTER", "INK",
        "BOOK", "GUIDE", "MANUAL", "COURSE",
    ]

    personal_keywords = [
        "SHIRT", "PANTS", "SHOES", "SOCKS", "UNDERWEAR", "JACKET",
        "TOY", "GAME", "SNACK", "FOOD", "KITCHEN", "BATHROOM",
        "SHAMPOO", "SOAP", "VITAMIN", "SUPPLEMENT", "PET ",
        "BABY ", "DIAPER", "CLEANING", "LAUNDRY",
    ]

    if any(k in name for k in business_keywords):
        return "business"
    if any(k in name for k in personal_keywords):
        return "personal"
    return None
