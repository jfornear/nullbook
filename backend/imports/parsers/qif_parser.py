"""QIF (Quicken Interchange Format) file parser for bank imports."""

from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_qif(file_content: str) -> dict:
    """Parse a QIF file and return structured data.

    QIF uses line-based records with single-character field prefixes:
      D = Date, T = Amount, P = Payee, M = Memo, N = Check number,
      L = Category, ^ = End of record

    Returns:
        {
            "headers": [...],
            "rows": [...],
            "row_count": int,
            "preview": [...first 5 rows...],
            "detected_mapping": {...},
            "account_type": str,
        }
    """
    lines = file_content.strip().splitlines()
    account_type = ""
    transactions = []
    current = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Account type header
        if line.startswith("!Type:"):
            account_type = line[6:].strip()
            continue
        if line.startswith("!"):
            continue

        # End of record
        if line == "^":
            if current:
                txn = _finalize_record(current)
                if txn:
                    transactions.append(txn)
                current = {}
            continue

        prefix = line[0]
        value = line[1:].strip()

        if prefix == "D":
            current["date"] = value
        elif prefix == "T":
            current["amount"] = value
        elif prefix == "U":
            # U is the amount in newer QIF versions (takes precedence)
            current["amount"] = value
        elif prefix == "P":
            current["payee"] = value
        elif prefix == "M":
            current["memo"] = value
        elif prefix == "N":
            current["check_number"] = value
        elif prefix == "L":
            current["category"] = value
        elif prefix == "C":
            current["cleared"] = value

    # Handle last record if no trailing ^
    if current:
        txn = _finalize_record(current)
        if txn:
            transactions.append(txn)

    headers = ["date", "amount", "description", "category"]
    rows = []
    for txn in transactions:
        rows.append({
            "date": txn["date"],
            "amount": txn["amount"],
            "description": txn["description"],
            "category": txn.get("category", ""),
        })

    return {
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "preview": rows[:5],
        "detected_mapping": {"date": "date", "amount": "amount", "description": "description"},
        "account_type": _map_qif_account_type(account_type),
        "format": "qif",
    }


def _finalize_record(record: dict) -> dict | None:
    """Convert a raw QIF record into a structured transaction dict."""
    date_str = record.get("date", "")
    amount_str = record.get("amount", "")

    if not date_str or not amount_str:
        return None

    date = _parse_qif_date(date_str)
    if not date:
        return None

    # Parse amount
    amount_str = amount_str.replace(",", "").replace("$", "").strip()
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        return None

    description = record.get("payee", "") or record.get("memo", "")

    return {
        "date": date.isoformat(),
        "amount": str(abs(amount)),
        "description": description,
        "type": "income" if amount > 0 else "expense",
        "category": record.get("category", ""),
    }


def _parse_qif_date(date_str: str) -> datetime | None:
    """Parse QIF date formats. Common: M/D/YYYY, M/D'YY, MM/DD/YYYY."""
    # Handle apostrophe year format (e.g., 1/31'24)
    date_str = date_str.replace("'", "/")

    for fmt in ["%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _map_qif_account_type(qif_type: str) -> str:
    """Map QIF account type to local account type."""
    mapping = {
        "Bank": "checking",
        "Cash": "cash",
        "CCard": "credit_card",
        "Invst": "investment",
        "Oth A": "other",
        "Oth L": "loan",
    }
    return mapping.get(qif_type, "checking")
