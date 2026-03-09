"""Subscription detection engine.

Analyzes transaction history to identify recurring charges and
track subscription services.
"""

import logging
import re
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)

# Prefixes to strip from merchant names for normalization
MERCHANT_PREFIXES = [
    r"^SQ \*",
    r"^TST \*",
    r"^SP \*",
    r"^PAYPAL \*",
    r"^GOOGLE \*",
    r"^APPLE\.COM/BILL",
    r"^AMZN ",
    r"^AMZ\*",
    r"^CKO\*",
    r"^FS \*",
    r"^DD ",
    r"^VENMO \*",
]

# Known subscription services with cancellation info
KNOWN_SUBSCRIPTIONS = {
    "netflix": {"cancellation_url": "https://www.netflix.com/cancelplan", "method": "web"},
    "hulu": {"cancellation_url": "https://secure.hulu.com/account", "method": "web"},
    "spotify": {"cancellation_url": "https://www.spotify.com/account/subscription/", "method": "web"},
    "apple": {"cancellation_url": "https://support.apple.com/en-us/HT202039", "method": "web"},
    "amazon prime": {"cancellation_url": "https://www.amazon.com/manageprime", "method": "web"},
    "disney+": {"cancellation_url": "https://www.disneyplus.com/account", "method": "web"},
    "hbo max": {"cancellation_url": "https://www.max.com/account", "method": "web"},
    "youtube": {"cancellation_url": "https://www.youtube.com/paid_memberships", "method": "web"},
    "adobe": {"cancellation_url": "https://account.adobe.com/plans", "method": "web"},
    "dropbox": {"cancellation_url": "https://www.dropbox.com/account/plan", "method": "web"},
}


def normalize_merchant_name(description: str) -> str:
    """Normalize a transaction description to extract the merchant name."""
    name = description.strip()
    for prefix in MERCHANT_PREFIXES:
        name = re.sub(prefix, "", name, flags=re.IGNORECASE).strip()
    # Remove trailing reference numbers
    name = re.sub(r"\s+#\d+$", "", name)
    name = re.sub(r"\s+\d{4,}$", "", name)
    # Remove city/state suffixes
    name = re.sub(r"\s+[A-Z]{2}\s+\d{5}$", "", name)
    return name.strip()


def detect_frequency(dates: list, amount: Decimal) -> dict | None:
    """Detect the billing frequency from a list of charge dates.

    Returns frequency info or None if no pattern detected.
    """
    if len(dates) < 2:
        return None

    sorted_dates = sorted(dates)
    gaps = []
    for i in range(1, len(sorted_dates)):
        gap = (sorted_dates[i] - sorted_dates[i - 1]).days
        gaps.append(gap)

    if not gaps:
        return None

    avg_gap = sum(gaps) / len(gaps)

    # Determine frequency based on average gap
    if 5 <= avg_gap <= 9:
        frequency = "weekly"
        expected_gap = 7
    elif 12 <= avg_gap <= 18:
        frequency = "biweekly"
        expected_gap = 14
    elif 26 <= avg_gap <= 35:
        frequency = "monthly"
        expected_gap = 30
    elif 85 <= avg_gap <= 100:
        frequency = "quarterly"
        expected_gap = 91
    elif 170 <= avg_gap <= 200:
        frequency = "semi_annual"
        expected_gap = 182
    elif 350 <= avg_gap <= 380:
        frequency = "annual"
        expected_gap = 365
    else:
        return None

    # Calculate confidence based on consistency
    variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
    std_dev = variance ** 0.5
    consistency = max(0, 1 - (std_dev / expected_gap))
    confidence = min(1.0, consistency * (min(len(dates), 6) / 6))

    # Detect amount changes
    return {
        "frequency": frequency,
        "avg_gap_days": round(avg_gap, 1),
        "confidence": round(confidence, 2),
        "charge_count": len(dates),
    }


def detect_subscriptions(user) -> list[dict]:
    """Analyze user's transactions to detect recurring subscriptions.

    Groups transactions by normalized merchant name, then checks for
    recurring patterns in the last 12 months.
    """
    from transactions.models import Transaction

    twelve_months_ago = timezone.now().date() - timedelta(days=365)

    # Get expense transactions from the last 12 months
    transactions = (
        Transaction.objects.filter(
            user=user,
            transaction_type="expense",
            date__gte=twelve_months_ago,
        )
        .values("description", "amount", "date", "category__name")
        .order_by("date")
    )

    # Group by normalized merchant name
    merchant_groups = defaultdict(lambda: {"amounts": [], "dates": [], "categories": set()})

    for txn in transactions:
        merchant = normalize_merchant_name(txn["description"])
        if not merchant:
            continue
        merchant_groups[merchant]["amounts"].append(txn["amount"])
        merchant_groups[merchant]["dates"].append(txn["date"])
        if txn["category__name"]:
            merchant_groups[merchant]["categories"].add(txn["category__name"])

    subscriptions = []

    for merchant, data in merchant_groups.items():
        if len(data["dates"]) < 2:
            continue

        # Check if amounts are consistent (subscription-like)
        amounts = data["amounts"]
        avg_amount = sum(amounts) / len(amounts)
        amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        amount_std = float(amount_variance ** Decimal("0.5"))

        # Skip if amounts vary too much (> 20% of average)
        if avg_amount > 0 and amount_std / float(avg_amount) > 0.20:
            continue

        freq_info = detect_frequency(data["dates"], avg_amount)
        if not freq_info or freq_info["confidence"] < 0.5:
            continue

        last_charged = max(data["dates"])
        # Calculate expected next charge
        gap_days = int(freq_info["avg_gap_days"])
        next_expected = last_charged + timedelta(days=gap_days)

        # Check if subscription might be cancelled (missed expected charge)
        days_overdue = (timezone.now().date() - next_expected).days
        if days_overdue > gap_days * 0.5:
            status = "possibly_cancelled"
        else:
            status = "active"

        # Look up known subscription info
        known_info = {}
        merchant_lower = merchant.lower()
        for known_name, info in KNOWN_SUBSCRIPTIONS.items():
            if known_name in merchant_lower:
                known_info = info
                break

        # Detect price changes
        price_change = None
        if len(amounts) >= 3:
            recent = amounts[-1]
            older = amounts[0]
            if recent != older:
                price_change = {
                    "old_amount": str(older),
                    "new_amount": str(recent),
                    "change": str(recent - older),
                }

        # Annual cost calculation
        multiplier = {"weekly": 52, "biweekly": 26, "monthly": 12, "quarterly": 4, "semi_annual": 2, "annual": 1}
        annual_cost = float(avg_amount) * multiplier.get(freq_info["frequency"], 12)

        subscriptions.append({
            "merchant": merchant,
            "amount": str(round(avg_amount, 2)),
            "frequency": freq_info["frequency"],
            "confidence": freq_info["confidence"],
            "last_charged": last_charged.isoformat(),
            "next_expected": next_expected.isoformat(),
            "status": status,
            "charge_count": freq_info["charge_count"],
            "category": list(data["categories"])[0] if data["categories"] else None,
            "annual_cost": round(annual_cost, 2),
            "price_change": price_change,
            "cancellation_url": known_info.get("cancellation_url"),
            "cancellation_method": known_info.get("method"),
        })

    # Sort by annual cost descending
    subscriptions.sort(key=lambda s: s["annual_cost"], reverse=True)
    return subscriptions
