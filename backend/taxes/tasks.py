"""Celery tasks for taxes app."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_receipt_task(receipt_id):
    """Process a receipt image through OCR."""
    from .models import Receipt
    from .services import process_receipt_image

    # Guard against duplicate processing (e.g. task queued twice)
    try:
        receipt = Receipt.objects.get(id=receipt_id)
    except Receipt.DoesNotExist:
        logger.warning("Receipt %s not found, skipping", receipt_id)
        return
    if receipt.status not in ("pending", "failed"):
        logger.info("Receipt %s already %s, skipping", receipt_id, receipt.status)
        return
    Receipt.objects.filter(id=receipt_id, status__in=["pending", "failed"]).update(status="processing")

    logger.info("Processing receipt %s", receipt_id)
    try:
        process_receipt_image(receipt_id)
        logger.info("Receipt %s processed successfully", receipt_id)

        # After OCR, attempt auto-matching to transactions
        try:
            from taxes.matching import auto_link_tax_year, match_receipt_to_transaction
            from taxes.models import Receipt

            receipt = Receipt.objects.get(id=receipt_id)
            match_receipt_to_transaction(receipt)
            auto_link_tax_year(receipt)
        except Exception:
            logger.exception("Auto-match failed for receipt %s", receipt_id)
    except Exception:
        logger.exception("Receipt %s processing failed", receipt_id)


@shared_task
def auto_match_receipts():
    """Match all unmatched receipts to transactions.

    Runs daily via Celery beat.
    """
    from django.contrib.auth import get_user_model

    from taxes.matching import batch_match_receipts

    User = get_user_model()
    results = []

    for user in User.objects.all():
        result = batch_match_receipts(user)
        results.append(f"{user.username}: matched {result['matched']}/{result['total']}")

    return "; ".join(results) or "No receipts to match"


@shared_task
def auto_detect_deductions():
    """Scan transactions for potentially deductible expenses.

    Runs weekly via Celery beat.
    """
    from django.utils import timezone

    from taxes.models import TaxYear

    current_year = timezone.now().year
    tax_years = TaxYear.objects.filter(year=current_year)

    for ty in tax_years:
        logger.info("Scanning deductions for %s (year %d)", ty.user.username, ty.year)
        # The scan_transactions_for_deductions tool handler already
        # implements this logic — this task just runs it on schedule
        from chat.tools import _scan_transactions_for_deductions
        result = _scan_transactions_for_deductions(ty.user, {"tax_year": ty.year})
        if "suggestions" in result:
            unclaimed = result.get("total_unclaimed", "0")
            logger.info(
                "Found $%s in potential unclaimed deductions for %s",
                unclaimed, ty.user.username,
            )

    return f"Scanned {tax_years.count()} tax years"


@shared_task
def quarterly_tax_reminder():
    """Send quarterly estimated tax payment reminders.

    Runs on schedule: Jan 15, Apr 15, Jun 15, Sep 15.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from core.models import Alert

    User = get_user_model()
    now = timezone.now()

    # Quarterly payment due dates
    quarters = {
        (1, 15): "Q4 (previous year)",
        (4, 15): "Q1",
        (6, 15): "Q2",
        (9, 15): "Q3",
    }

    for (month, day), quarter in quarters.items():
        if now.month == month and now.day <= day and now.day >= day - 7:
            title = f"Quarterly tax payment due ({quarter})"
            for user in User.objects.all():
                if Alert.objects.filter(
                    user=user,
                    alert_type="tax_reminder",
                    title=title,
                    created_at__date=now.date(),
                ).exists():
                    continue
                Alert.objects.create(
                    user=user,
                    alert_type="tax_reminder",
                    severity="warning",
                    title=title,
                    message=(
                        f"Estimated tax payment for {quarter} is due on "
                        f"{now.year}-{month:02d}-{day:02d}. Use the tax estimation tool "
                        f"to calculate your quarterly payment."
                    ),
                )
            return f"Sent {quarter} tax reminder"

    return "No quarterly reminder needed today"
