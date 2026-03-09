"""Email sending for subscription cancellation and notifications."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

logger = logging.getLogger(__name__)


def send_cancellation_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: str | None = None,
    email_account=None,
) -> dict:
    """Send a cancellation email via SMTP.

    Args:
        to_email: Recipient email address.
        subject: Email subject.
        body: Email body text.
        from_email: Sender email (defaults to SMTP_USER).
        email_account: Unused, kept for API compatibility.

    Returns:
        dict with success status and message_id.
    """
    return _send_via_smtp(to_email, subject, body, from_email)


def _send_via_smtp(to_email: str, subject: str, body: str, from_email: str | None = None) -> dict:
    """Send email via SMTP."""
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    user = settings.SMTP_USER
    password = settings.SMTP_PASSWORD

    if not host or not user:
        return {"success": False, "error": "SMTP not configured. Set SMTP_HOST and SMTP_USER in .env"}

    sender = from_email or user

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        logger.info("Sent cancellation email to %s: %s", to_email, subject)
        return {"success": True, "message_id": msg["Message-ID"]}
    except Exception as e:
        logger.exception("Failed to send email to %s", to_email)
        return {"success": False, "error": str(e)}


def generate_cancellation_email(merchant: str, subscription_amount: str, user_name: str = "") -> dict:
    """Generate a cancellation email template for a subscription.

    Returns subject and body text for user review before sending.
    """
    subject = f"Cancellation Request — {merchant} Subscription"

    body = f"""Dear {merchant} Support,

I am writing to request the cancellation of my subscription service.

Account Details:
- Service: {merchant}
- Recurring Amount: ${subscription_amount}
{f'- Account Holder: {user_name}' if user_name else ''}

Please cancel my subscription effective immediately and confirm that no further charges will be made to my payment method.

Please send confirmation of this cancellation to this email address.

Thank you for your assistance.

Best regards{f', {user_name}' if user_name else ''}"""

    return {
        "subject": subject,
        "body": body,
    }
