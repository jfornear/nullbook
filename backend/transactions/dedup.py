"""Duplicate transaction detection."""


from transactions.models import Transaction


def _normalize(s):
    """Normalize description for comparison."""
    return "".join(c.lower() for c in s if c.isalnum())


def find_potential_duplicates(user, day_tolerance=1):
    """Find potential duplicate transaction pairs.

    A pair is considered a potential duplicate if:
    - Same amount
    - Dates within day_tolerance days
    - Normalized descriptions share a substring of at least 6 chars
    """
    txns = list(
        Transaction.objects.filter(user=user)
        .select_related("category", "account")
        .order_by("date", "amount")[:2000]
    )

    pairs = []
    seen = set()

    for i, a in enumerate(txns):
        for j in range(i + 1, len(txns)):
            b = txns[j]
            # Stop scanning if dates are too far apart
            if (b.date - a.date).days > day_tolerance:
                break

            if a.amount != b.amount:
                continue

            pair_key = (min(a.id, b.id), max(a.id, b.id))
            if pair_key in seen:
                continue

            norm_a = _normalize(a.description)
            norm_b = _normalize(b.description)

            # Check for substring overlap (min 6 chars)
            match = False
            min_len = min(len(norm_a), len(norm_b))
            check_len = min(6, min_len)
            if check_len >= 4:
                for k in range(len(norm_a) - check_len + 1):
                    if norm_a[k:k + check_len] in norm_b:
                        match = True
                        break

            if not match and norm_a == norm_b:
                match = True

            if match:
                seen.add(pair_key)
                confidence = 0.7
                if a.date == b.date:
                    confidence += 0.15
                if norm_a == norm_b:
                    confidence += 0.15

                pairs.append({
                    "transaction_a": {
                        "id": a.id,
                        "date": a.date.isoformat(),
                        "description": a.description,
                        "amount": str(a.amount),
                        "account": a.account.name if a.account else None,
                        "category": a.category.name if a.category else None,
                    },
                    "transaction_b": {
                        "id": b.id,
                        "date": b.date.isoformat(),
                        "description": b.description,
                        "amount": str(b.amount),
                        "account": b.account.name if b.account else None,
                        "category": b.category.name if b.category else None,
                    },
                    "confidence": round(confidence, 2),
                })

    pairs.sort(key=lambda p: -p["confidence"])
    return pairs[:50]
