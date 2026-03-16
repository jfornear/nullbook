"""CSV file parser for transaction imports."""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from imports.parsers.bank_profiles import detect_bank_profile


def parse_csv(file_content: str, filename: str = "") -> dict:
    """Parse a CSV file and return structured data.

    Returns:
        {
            "headers": [...],
            "rows": [...],
            "row_count": int,
            "preview": [...first 5 rows...],
            "detected_mapping": {...suggested column mapping...},
            "bank_profile": str | None,
            "bank_profile_name": str | None,
            "source_institution": str | None,
        }
    """
    reader = csv.DictReader(io.StringIO(file_content))
    headers = reader.fieldnames or []
    rows = list(reader)

    # Try bank profile detection first
    profile = detect_bank_profile(headers, filename)

    if profile:
        mapping = dict(profile.column_mapping)
        # For Capital One with separate Debit/Credit columns, handle specially
        if profile.id == "capital_one" and "Debit" in headers:
            mapping["amount"] = "Debit"  # Will be handled in apply_mapping
    else:
        mapping = detect_column_mapping(headers)

    result = {
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "preview": rows[:5],
        "detected_mapping": mapping,
        "bank_profile": profile.id if profile else None,
        "bank_profile_name": profile.name if profile else None,
        "source_institution": profile.institution_name if profile else None,
    }

    return result


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


def apply_mapping(rows: list[dict], mapping: dict, bank_profile_id: str = "") -> dict:
    """Transform raw CSV rows into transaction-ready dicts using the column mapping.

    Args:
        rows: Raw CSV rows as list of dicts.
        mapping: Column mapping (internal field -> CSV header).
        bank_profile_id: Optional bank profile ID for bank-specific handling.

    Returns:
        {"transactions": list[dict], "errors": list[str]}
    """
    from imports.parsers.bank_profiles import PROFILES_BY_ID

    profile = PROFILES_BY_ID.get(bank_profile_id)
    amount_inverted = profile.amount_inverted if profile else False

    # Capital One has separate Debit/Credit columns
    is_capital_one = bank_profile_id == "capital_one"

    transactions = []
    errors = []

    for i, row in enumerate(rows):
        try:
            date_str = row.get(mapping.get("date", ""), "").strip()
            description = row.get(mapping.get("description", ""), "").strip()

            # Handle Capital One's separate Debit/Credit columns
            if is_capital_one:
                debit_str = row.get("Debit", "").strip()
                credit_str = row.get("Credit", "").strip()
                if debit_str:
                    amount_str = debit_str
                elif credit_str:
                    amount_str = credit_str
                else:
                    errors.append(f"Row {i+1}: No amount found in Debit or Credit column")
                    continue
            else:
                amount_str = row.get(mapping.get("amount", ""), "").strip()

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

            # Amex and similar: charges are positive, need to negate
            if amount_inverted:
                amount = -amount

            # For Capital One: Debit column is positive for charges
            if is_capital_one and row.get("Debit", "").strip():
                amount = -abs(amount)
            elif is_capital_one and row.get("Credit", "").strip():
                amount = abs(amount)

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
