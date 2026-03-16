"""Transaction description anonymization.

Strips account numbers, reference IDs, and other PII from transaction
descriptions while preserving merchant names for categorization.
"""

import csv
import io
import re


def anonymize_description(description: str) -> str:
    """Strip PII from a transaction description while preserving the merchant name.

    Redacts:
    - Trailing reference/card numbers (#1234...)
    - Long digit sequences (6+ digits, avoiding dates)
    - PPD ID, WEB ID, TEL ID, CCD ID patterns
    - Hex-like transaction IDs (8+ hex chars)
    - Normalizes whitespace
    """
    d = description
    # Remove trailing reference/card numbers
    d = re.sub(r'#\d{4,}', '#XXXX', d)
    # Remove sequences of 6+ digits (account/ref numbers, not dates)
    d = re.sub(r'\b\d{6,}\b', 'XXXXXX', d)
    # Remove common PII patterns in checking descriptions
    d = re.sub(r'(PPD ID|WEB ID|TEL ID|CCD ID):?\s*\S+', r'\1: REDACTED', d, flags=re.IGNORECASE)
    # Remove specific transaction IDs (hex-like)
    d = re.sub(r'[A-F0-9]{8,}', 'REDACTED', d, flags=re.IGNORECASE)
    # Clean up extra whitespace
    d = re.sub(r'\s+', ' ', d).strip()
    return d


def export_anonymized_csv(transactions) -> str:
    """Export transactions as an anonymized CSV string.

    Args:
        transactions: QuerySet or list of Transaction objects with
            date, description, amount, transaction_type attributes.

    Returns:
        CSV string with anonymized descriptions.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Amount", "Type"])

    for txn in transactions:
        writer.writerow([
            str(txn.date),
            anonymize_description(txn.description),
            str(txn.amount),
            txn.transaction_type,
        ])

    return output.getvalue()
