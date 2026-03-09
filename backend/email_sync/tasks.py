"""Celery tasks for email scanning."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def scan_email_for_receipts():
    """Scheduled task: scan all active EmailAccounts for new receipts."""
    from .models import EmailAccount

    active_accounts = list(EmailAccount.objects.filter(status="active").values_list("id", flat=True))
    logger.info("Starting scheduled email scan for %d active accounts", len(active_accounts))

    for account_id in active_accounts:
        # Dispatch each account scan as a separate retriable task
        scan_single_email_account.delay(account_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_single_email_account(self, email_account_id):
    """Scan a single email account for new receipts.

    Args:
        email_account_id: PK of the EmailAccount to scan.
    """
    from .scanner import scan_email_account

    logger.info("Scanning single email account %s", email_account_id)
    try:
        scan_email_account(email_account_id)
    except Exception as exc:
        logger.exception("Failed to scan email account %s", email_account_id)
        raise self.retry(exc=exc)
