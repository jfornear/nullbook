"""Celery tasks for transaction automation."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def detect_subscriptions():
    """Detect subscriptions from transaction history and update Subscription records.

    Runs daily via Celery beat. Compares detected subscriptions against
    existing records and creates/updates as needed.
    """
    from django.contrib.auth import get_user_model

    from transactions.models import Category, Subscription
    from transactions.subscriptions import detect_subscriptions as _detect

    User = get_user_model()
    total_updated = 0

    for user in User.objects.all():
        detected = _detect(user)

        for sub_data in detected:
            category = None
            if sub_data.get("category"):
                category = Category.objects.filter(name=sub_data["category"]).first()

            defaults = {
                "amount": sub_data["amount"],
                "frequency": sub_data["frequency"],
                "confidence": sub_data["confidence"],
                "last_charged": sub_data["last_charged"],
                "next_expected": sub_data["next_expected"],
                "category": category,
            }

            # Only update status if not manually set
            sub, created = Subscription.objects.get_or_create(
                user=user,
                merchant=sub_data["merchant"],
                defaults={
                    **defaults,
                    "status": sub_data["status"],
                    "cancellation_url": sub_data.get("cancellation_url") or "",
                    "cancellation_method": sub_data.get("cancellation_method") or "",
                },
            )

            if not created:
                # Update amounts and dates but preserve manual status changes
                if sub.status not in ("cancelled", "cancellation_pending"):
                    sub.status = sub_data["status"]
                sub.amount = sub_data["amount"]
                sub.frequency = sub_data["frequency"]
                sub.confidence = sub_data["confidence"]
                sub.last_charged = sub_data["last_charged"]
                sub.next_expected = sub_data["next_expected"]
                if sub_data.get("cancellation_url") and not sub.cancellation_url:
                    sub.cancellation_url = sub_data["cancellation_url"]
                sub.save()

            total_updated += 1

    return f"Updated {total_updated} subscriptions"


@shared_task
def auto_categorize_transactions():
    """Categorize uncategorized transactions using rules and AI.

    Runs daily via Celery beat.
    """
    from django.contrib.auth import get_user_model

    from transactions.categorizer import batch_categorize_transactions

    User = get_user_model()
    results = []

    for user in User.objects.all():
        result = batch_categorize_transactions(user)
        results.append(f"{user.username}: {result['message']}")
        logger.info("Auto-categorize for %s: %s", user.username, result["message"])

    return "; ".join(results)
