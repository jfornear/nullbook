"""Shared scanning logic for email receipt extraction."""

import logging
import re
from email.utils import parsedate_to_datetime

from django.core.files.base import ContentFile
from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)

# Content types eligible for receipt processing
RECEIPT_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
}


def scan_email_account(email_account_id):
    """Main entry point: scan an email account for receipt-like messages.

    1. Get EmailAccount, determine provider
    2. Search for new messages since last_synced_at
    3. For each message, check against EmailRules (ordered by priority)
    4. If matched and action is process_receipt:
       - Extract attachments
       - For image/PDF attachments, create Receipt + trigger processing
    5. Create EmailMessage records
    6. Update last_synced_at

    Args:
        email_account_id: PK of the EmailAccount to scan.
    """
    from .models import EmailAccount, EmailRule

    try:
        email_account = EmailAccount.objects.get(pk=email_account_id, status="active")
    except EmailAccount.DoesNotExist:
        logger.warning("EmailAccount %s not found or not active", email_account_id)
        return

    user = email_account.user
    rules = EmailRule.objects.filter(user=user, is_active=True).order_by("-priority")
    since = email_account.last_synced_at

    logger.info(
        "Scanning email account %s (provider=%s, since=%s)",
        email_account.email_address,
        email_account.provider,
        since,
    )

    try:
        _scan_imap(email_account, rules, since)

        email_account.last_synced_at = dj_timezone.now()
        email_account.status = "active"
        email_account.error_message = ""
        email_account.save(update_fields=["last_synced_at", "status", "error_message"])

    except Exception as exc:
        logger.exception("Error scanning email account %s", email_account_id)
        email_account.status = "error"
        email_account.error_message = str(exc)[:2000]
        email_account.save(update_fields=["status", "error_message"])


def _scan_imap(email_account, rules, since):
    """Scan an IMAP account for new messages."""
    from . import imap_client
    from .models import EmailMessage

    conn = imap_client.connect_imap(email_account)

    try:
        msg_ids = imap_client.search_messages(conn, criteria="ALL", since_date=since)

        for msg_id in msg_ids:
            msg = imap_client.fetch_message(conn, msg_id)
            if msg is None:
                continue

            message_id = msg.get("Message-ID", f"imap-{email_account.id}-{msg_id.decode()}")
            from_address = msg.get("From", "")
            subject = msg.get("Subject", "")
            date_str = msg.get("Date", "")

            # Skip if already processed
            if EmailMessage.objects.filter(message_id=message_id).exists():
                continue

            try:
                msg_date = parsedate_to_datetime(date_str) if date_str else dj_timezone.now()
            except (ValueError, TypeError):
                msg_date = dj_timezone.now()

            attachments = imap_client.get_attachments(msg)
            has_attachments = len(attachments) > 0

            matched_rule = match_rules(rules, from_address, subject, has_attachments)
            action_taken = ""

            if matched_rule and matched_rule.action == "process_receipt":
                for att in attachments:
                    if att["content_type"] in RECEIPT_CONTENT_TYPES:
                        receipt = create_receipt_from_attachment(
                            email_account.user,
                            att["data"],
                            att["filename"],
                            att["content_type"],
                        )
                        action_taken = f"created_receipt:{receipt.id}"
            elif matched_rule and matched_rule.action == "ignore":
                action_taken = "ignored"

            email_msg = EmailMessage.objects.create(
                email_account=email_account,
                message_id=message_id,
                from_address=from_address,
                subject=subject,
                date=msg_date,
                matched_rule=matched_rule,
                is_processed=True,
                action_taken=action_taken,
            )

            _save_attachment_records(email_msg, attachments, email_account.user)

    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _save_attachment_records(email_msg, attachments, user):
    """Save EmailAttachment records for downloaded attachments."""
    from .models import EmailAttachment

    for att in attachments:
        file_content = ContentFile(att["data"], name=att["filename"])
        EmailAttachment.objects.create(
            email_message=email_msg,
            filename=att["filename"],
            content_type=att["content_type"],
            file=file_content,
        )


def match_rules(rules, from_addr, subject, has_attachments):
    """Find the first matching EmailRule for a message.

    Rules are expected to be ordered by -priority already.

    Args:
        rules: QuerySet of EmailRule objects.
        from_addr: Sender address/name string.
        subject: Email subject string.
        has_attachments: Boolean indicating if the email has attachments.

    Returns:
        The first matching EmailRule, or None.
    """
    for rule in rules:
        # Check from_pattern
        if rule.from_pattern:
            try:
                if not re.search(rule.from_pattern, from_addr, re.IGNORECASE):
                    continue
            except re.error:
                logger.warning("Bad regex in email rule %s from_pattern", rule.id)
                continue

        # Check subject_pattern
        if rule.subject_pattern:
            try:
                if not re.search(rule.subject_pattern, subject, re.IGNORECASE):
                    continue
            except re.error:
                logger.warning("Bad regex in email rule %s subject_pattern", rule.id)
                continue

        # Check has_attachment
        if rule.has_attachment is not None:
            if rule.has_attachment != has_attachments:
                continue

        return rule

    return None


def create_receipt_from_attachment(user, attachment_data, filename, content_type):
    """Save an attachment file and create a Receipt for OCR processing.

    Args:
        user: User instance who owns the receipt.
        attachment_data: Raw file bytes.
        filename: Original filename.
        content_type: MIME type of the attachment.

    Returns:
        The created Receipt instance.
    """
    from taxes.models import Receipt
    from taxes.tasks import process_receipt_task

    file_content = ContentFile(attachment_data, name=filename)
    receipt = Receipt.objects.create(
        user=user,
        image=file_content,
        status="pending",
    )

    logger.info(
        "Created receipt %s from email attachment: %s",
        receipt.id,
        filename,
    )

    process_receipt_task.delay(receipt.id)
    return receipt
