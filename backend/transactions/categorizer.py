"""Smart auto-categorization using AI and learned rules.

Categorizes uncategorized transactions in batch using AI,
and learns from user corrections to improve over time.
"""

import logging

logger = logging.getLogger(__name__)


def batch_categorize_transactions(user, transaction_ids: list[int] | None = None, limit: int = 50):
    """Categorize uncategorized transactions using AI.

    Args:
        user: The user whose transactions to categorize.
        transaction_ids: Specific transaction IDs. If None, finds uncategorized ones.
        limit: Max transactions per batch.

    Returns:
        dict with categorized count and details.
    """
    from chat.llm_client import LLMClient

    from transactions.models import Category, CategoryRule, Transaction

    # Get transactions to categorize
    if transaction_ids:
        qs = Transaction.objects.filter(id__in=transaction_ids, user=user)
    else:
        qs = Transaction.objects.filter(user=user, category__isnull=True)

    transactions = list(qs[:limit])
    if not transactions:
        return {"categorized": 0, "message": "No uncategorized transactions found."}

    # First, try rule-based categorization
    rules = CategoryRule.objects.filter(user=user).select_related("category")
    rule_categorized = 0
    remaining = []

    for txn in transactions:
        matched = False
        for rule in rules:
            if rule.pattern.lower() in txn.description.lower():
                txn.category = rule.category
                txn.save(update_fields=["category", "updated_at"])
                rule_categorized += 1
                matched = True
                break
        if not matched:
            remaining.append(txn)

    if not remaining:
        return {
            "categorized": rule_categorized,
            "rule_matched": rule_categorized,
            "ai_categorized": 0,
            "message": f"Categorized {rule_categorized} transactions using rules.",
        }

    # Get available categories
    categories = list(Category.objects.filter(parent__isnull=True).values_list("name", flat=True))
    if not categories:
        return {"categorized": rule_categorized, "message": "No categories available."}

    # Build the batch prompt for the LLM
    txn_list = "\n".join(
        f"- ID:{t.id} | {t.date} | ${t.amount} | {t.description}"
        for t in remaining
    )

    prompt = f"""Categorize these financial transactions. Available categories: {', '.join(categories)}

Transactions:
{txn_list}

Respond with one line per transaction in the format: ID:category_name
Only use categories from the list above. If unsure, use the closest match."""

    try:
        llm = LLMClient()
        result_text = llm.complete(messages=[{"role": "user", "content": prompt}])
    except Exception:
        logger.exception("AI categorization failed")
        return {
            "categorized": rule_categorized,
            "rule_matched": rule_categorized,
            "ai_categorized": 0,
            "message": f"Rule-matched {rule_categorized}. AI categorization failed.",
        }

    # Parse response and apply categories
    category_objs = {c.name.lower(): c for c in Category.objects.filter(parent__isnull=True)}
    txn_map = {t.id: t for t in remaining}
    ai_categorized = 0

    for line in result_text.strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        try:
            id_part, cat_part = line.split(":", 1)
            txn_id = int(id_part.strip().replace("ID", ""))
            cat_name = cat_part.strip().lower()

            if txn_id in txn_map and cat_name in category_objs:
                txn = txn_map[txn_id]
                txn.category = category_objs[cat_name]
                txn.save(update_fields=["category", "updated_at"])
                ai_categorized += 1
        except (ValueError, KeyError):
            continue

    total = rule_categorized + ai_categorized
    return {
        "categorized": total,
        "rule_matched": rule_categorized,
        "ai_categorized": ai_categorized,
        "message": f"Categorized {total} transactions ({rule_categorized} by rules, {ai_categorized} by AI).",
    }


def categorize_for_taxes(user, tax_year: int, limit: int = 5000):
    """Run Schedule C business categorization on transactions for a tax year.

    This uses the keyword-based categorizer (not AI) to classify
    transactions into tax categories like 'Software & SaaS', 'Travel',
    'Meals', etc.
    """
    from transactions.business_categorizer import batch_categorize_for_taxes
    return batch_categorize_for_taxes(user, tax_year, limit)


def learn_from_correction(user, transaction_id: int, new_category_id: int):
    """When a user re-categorizes a transaction, create a rule automatically."""
    from transactions.models import Category, CategoryRule, Transaction

    try:
        txn = Transaction.objects.get(id=transaction_id, user=user)
        category = Category.objects.get(id=new_category_id)
    except (Transaction.DoesNotExist, Category.DoesNotExist):
        return

    # Normalize the description for the pattern
    pattern = txn.description.strip()
    # Remove trailing numbers/references for a more general pattern
    import re
    pattern = re.sub(r"\s+#?\d{4,}$", "", pattern).strip()

    if not pattern:
        return

    # Create or update rule
    CategoryRule.objects.update_or_create(
        user=user,
        pattern=pattern,
        defaults={
            "category": category,
            "auto_generated": True,
        },
    )
