"""OFX/QFX file format parser for bank statement imports."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_ofx(file_content: str) -> dict:
    """Parse an OFX/QFX file and return structured data.

    OFX (Open Financial Exchange) is an XML-like format used by banks
    for downloading transaction data. QFX is Quicken's variant.

    Returns:
        {
            "headers": [...],
            "rows": [...],
            "row_count": int,
            "preview": [...first 5 rows...],
            "detected_mapping": {...},
            "account_info": {...},
        }
    """
    transactions = _extract_transactions(file_content)
    account_info = _extract_account_info(file_content)

    headers = ["date", "amount", "description", "type", "fitid"]
    rows = []
    for txn in transactions:
        rows.append({
            "date": txn["date"],
            "amount": txn["amount"],
            "description": txn["description"],
            "type": txn["type"],
            "fitid": txn["fitid"],
        })

    return {
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "preview": rows[:5],
        "detected_mapping": {"date": "date", "amount": "amount", "description": "description"},
        "account_info": account_info,
        "format": "ofx",
    }


def _extract_transactions(content: str) -> list[dict]:
    """Extract transaction records from OFX content."""
    transactions = []

    # Find all STMTTRN blocks
    pattern = r"<STMTTRN>(.*?)</STMTTRN>"
    blocks = re.findall(pattern, content, re.DOTALL)

    # If no XML-style closing tags, try SGML-style (no closing tags)
    if not blocks:
        blocks = re.split(r"<STMTTRN>", content)[1:]
        blocks = [b.split("</STMTTRN>")[0] if "</STMTTRN>" in b else b.split("<STMTTRN>")[0] for b in blocks]

    for block in blocks:
        txn = _parse_transaction_block(block)
        if txn:
            transactions.append(txn)

    return transactions


def _parse_transaction_block(block: str) -> dict | None:
    """Parse a single STMTTRN block into a transaction dict."""
    date_str = _extract_tag(block, "DTPOSTED")
    amount_str = _extract_tag(block, "TRNAMT")
    name = _extract_tag(block, "NAME") or _extract_tag(block, "MEMO") or ""
    memo = _extract_tag(block, "MEMO") or ""
    fitid = _extract_tag(block, "FITID") or ""
    trntype = _extract_tag(block, "TRNTYPE") or ""

    if not date_str or not amount_str:
        return None

    # Parse OFX date format: YYYYMMDDHHMMSS or YYYYMMDD
    date = _parse_ofx_date(date_str)
    if not date:
        return None

    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        return None

    description = name if name else memo
    # Clean up description
    description = description.strip()

    return {
        "date": date.isoformat(),
        "amount": str(abs(amount)),
        "description": description,
        "type": "income" if amount > 0 else "expense",
        "fitid": fitid,
        "trntype": trntype,
    }


def _extract_tag(content: str, tag: str) -> str | None:
    """Extract value of an OFX tag (handles both SGML and XML style)."""
    # XML style: <TAG>value</TAG>
    match = re.search(rf"<{tag}>(.*?)</{tag}>", content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # SGML style: <TAG>value\n
    match = re.search(rf"<{tag}>([^\n<]+)", content)
    if match:
        return match.group(1).strip()

    return None


def _parse_ofx_date(date_str: str) -> datetime | None:
    """Parse OFX date formats."""
    # Remove timezone info in brackets
    date_str = re.sub(r"\[.*?\]", "", date_str).strip()

    for fmt in ["%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"]:
        try:
            return datetime.strptime(date_str[:len(fmt.replace("%", ""))], fmt)
        except (ValueError, IndexError):
            continue
    return None


def _extract_account_info(content: str) -> dict:
    """Extract account information from OFX header."""
    return {
        "bank_id": _extract_tag(content, "BANKID") or "",
        "account_id": _extract_tag(content, "ACCTID") or "",
        "account_type": _extract_tag(content, "ACCTTYPE") or "",
        "balance": _extract_tag(content, "BALAMT") or "",
        "balance_date": _extract_tag(content, "DTASOF") or "",
    }
