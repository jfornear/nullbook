"""Generic IMAP integration for email scanning."""

import email
import imaplib
import logging

logger = logging.getLogger(__name__)


def connect_imap(email_account):
    """Create an authenticated IMAP connection.

    Args:
        email_account: EmailAccount instance with provider='imap'.

    Returns:
        imaplib.IMAP4_SSL connection.

    Raises:
        imaplib.IMAP4.error: On connection or authentication failure.
    """
    creds = email_account.credentials
    host = email_account.imap_host
    port = email_account.imap_port

    logger.info("Connecting to IMAP server %s:%s", host, port)
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(creds.get("username", ""), creds.get("password", ""))
    conn.select("INBOX")
    return conn


def search_messages(conn, criteria="ALL", since_date=None):
    """Search IMAP mailbox for messages matching criteria.

    Args:
        conn: IMAP connection from connect_imap().
        criteria: IMAP search criteria string (e.g. 'UNSEEN', 'ALL').
        since_date: Optional datetime; only return messages since this date.

    Returns:
        List of IMAP message IDs (byte strings).
    """
    search_parts = []

    if since_date:
        date_str = since_date.strftime("%d-%b-%Y")
        search_parts.append(f"SINCE {date_str}")

    if criteria and criteria != "ALL":
        search_parts.append(criteria)

    search_query = " ".join(search_parts) if search_parts else "ALL"

    logger.info("IMAP search: %s", search_query)
    status, data = conn.search(None, search_query)

    if status != "OK":
        logger.error("IMAP search failed: %s", status)
        return []

    message_ids = data[0].split() if data[0] else []
    logger.info("IMAP search returned %d messages", len(message_ids))
    return message_ids


def fetch_message(conn, msg_id):
    """Fetch and parse a single email message.

    Args:
        conn: IMAP connection from connect_imap().
        msg_id: IMAP message ID (byte string).

    Returns:
        email.message.Message object, or None on failure.
    """
    status, data = conn.fetch(msg_id, "(RFC822)")

    if status != "OK":
        logger.error("Failed to fetch message %s: %s", msg_id, status)
        return None

    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)
    return msg


def get_attachments(msg):
    """Extract attachment files from an email.message.Message.

    Args:
        msg: email.message.Message object.

    Returns:
        List of dicts: {filename, content_type, data (bytes)}.
    """
    attachments = []

    if not msg.is_multipart():
        return attachments

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" not in content_disposition:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        content_type = part.get_content_type()
        data = part.get_payload(decode=True)

        if data:
            attachments.append({
                "filename": filename,
                "content_type": content_type,
                "data": data,
            })

    logger.info("Extracted %d attachments from email", len(attachments))
    return attachments
