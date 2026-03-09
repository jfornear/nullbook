"""CSV file parser for transaction imports."""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_csv(file_content: str) -> dict:
    """Parse a CSV file and return structured data.

    Returns:
        {
            "headers": [...],
            "rows": [...],
            "row_count": int,
            "preview": [...first 5 rows...],
            "detected_mapping": {...suggested column mapping...}
        }
    """
    reader = csv.DictReader(io.StringIO(file_content))
    headers = reader.fieldnames or []
    rows = list(reader)

    # Try to auto-detect column mappings
    mapping = detect_column_mapping(headers)

    return {
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "preview": rows[:5],
        "detected_mapping": mapping,
    }


def detect_column_mapping(headers: list[str]) -> dict:
    """Guess which CSV columns map to transaction fields."""
    mapping = {}
    header_lower = {h: h.lower().strip() for h in headers}

    date_keywords = ["date", "posted", "transaction date", "posting date"]
    amount_keywords = ["amount", "debit", "credit", "value", "sum"]
    desc_keywords = ["description", "memo", "details", "narrative", "payee", "name"]

    for original, lower in header_lower.items():
        if any(k in lower for k in date_keywords) and "date" not in mapping:
            mapping["date"] = original
        elif any(k in lower for k in amount_keywords) and "amount" not in mapping:
            mapping["amount"] = original
        elif any(k in lower for k in desc_keywords) and "description" not in mapping:
            mapping["description"] = original

    return mapping


def apply_mapping(rows: list[dict], mapping: dict) -> dict:
    """Transform raw CSV rows into transaction-ready dicts using the column mapping.

    Returns:
        {"transactions": list[dict], "errors": list[str]}
    """
    transactions = []
    errors = []

    for i, row in enumerate(rows):
        try:
            date_str = row.get(mapping.get("date", ""), "").strip()
            amount_str = row.get(mapping.get("amount", ""), "").strip()
            description = row.get(mapping.get("description", ""), "").strip()

            # Try common date formats
            date = None
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue

            if date is None:
                errors.append(f"Row {i+1}: Could not parse date '{date_str}'")
                continue

            # Parse amount (handle negative, parentheses, currency symbols)
            amount_str = amount_str.replace("$", "").replace(",", "").strip()
            if amount_str.startswith("(") and amount_str.endswith(")"):
                amount_str = "-" + amount_str[1:-1]

            amount = Decimal(amount_str)

            transaction_type = "income" if amount > 0 else "expense"

            transactions.append({
                "date": date.isoformat(),
                "amount": str(abs(amount)),
                "description": description,
                "transaction_type": transaction_type,
            })
        except (InvalidOperation, KeyError, ValueError) as e:
            errors.append(f"Row {i+1}: {str(e)}")

    return {"transactions": transactions, "errors": errors}
