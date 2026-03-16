"""Bank-specific import profiles for auto-detecting CSV formats.

Each profile defines the expected headers, column mapping, date format,
and other bank-specific quirks so users don't have to manually map columns.
"""

import re
from dataclasses import dataclass, field


@dataclass
class BankProfile:
    id: str
    name: str
    institution_name: str
    account_type: str  # "credit_card", "checking", "savings"
    header_signature: list[str]  # exact headers that identify this format
    column_mapping: dict[str, str]  # internal field -> CSV header
    date_format: str = "%m/%d/%Y"
    amount_inverted: bool = False  # True if charges are positive (need to negate)
    filename_pattern: str = ""  # regex pattern to match filenames
    extra_columns: list[str] = field(default_factory=list)  # columns to preserve as metadata


BANK_PROFILES: list[BankProfile] = [
    BankProfile(
        id="chase_credit",
        name="Chase Credit Card",
        institution_name="Chase",
        account_type="credit_card",
        header_signature=["Transaction Date", "Post Date", "Description", "Category", "Type", "Amount", "Memo"],
        column_mapping={"date": "Transaction Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=False,  # Chase credit: negative = charge, positive = payment/credit
        filename_pattern=r"Chase\d{4}",
        extra_columns=["Category", "Type", "Memo"],
    ),
    BankProfile(
        id="chase_checking",
        name="Chase Checking",
        institution_name="Chase",
        account_type="checking",
        header_signature=["Details", "Posting Date", "Description", "Amount", "Type", "Balance", "Check or Slip #"],
        column_mapping={"date": "Posting Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=False,
        filename_pattern=r"Chase\d{4}",
        extra_columns=["Details", "Type", "Balance"],
    ),
    BankProfile(
        id="capital_one",
        name="Capital One",
        institution_name="Capital One",
        account_type="credit_card",
        header_signature=["Transaction Date", "Posted Date", "Card No.", "Description", "Category", "Debit", "Credit"],
        column_mapping={"date": "Transaction Date", "description": "Description"},
        date_format="%Y-%m-%d",
        amount_inverted=False,
        extra_columns=["Category", "Card No."],
    ),
    BankProfile(
        id="bass_pro",
        name="Bass Pro / Cabela's",
        institution_name="Bass Pro Shops",
        account_type="credit_card",
        header_signature=["Date", "Description", "Amount", "Balance"],
        column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=False,
        filename_pattern=r"(?i)bass.?pro|cabela",
    ),
    BankProfile(
        id="amex",
        name="American Express",
        institution_name="American Express",
        account_type="credit_card",
        header_signature=["Date", "Description", "Amount", "Extended Details", "Appears On Your Statement As",
                          "Address", "City/State", "Zip Code", "Country", "Reference", "Category"],
        column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=True,  # Amex: charges are positive
        extra_columns=["Category", "Extended Details"],
    ),
    # Amex also has a simpler format — only match if filename hints at Amex
    BankProfile(
        id="amex_simple",
        name="American Express",
        institution_name="American Express",
        account_type="credit_card",
        header_signature=["Date", "Description", "Amount"],
        column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=True,
        filename_pattern=r"(?i)amex|american.?express",
    ),
    BankProfile(
        id="bank_of_america",
        name="Bank of America",
        institution_name="Bank of America",
        account_type="checking",
        header_signature=["Date", "Description", "Amount", "Running Bal."],
        column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=False,
    ),
    BankProfile(
        id="bank_of_america_credit",
        name="Bank of America Credit Card",
        institution_name="Bank of America",
        account_type="credit_card",
        header_signature=["Posted Date", "Reference Number", "Payee", "Address", "Amount"],
        column_mapping={"date": "Posted Date", "amount": "Amount", "description": "Payee"},
        date_format="%m/%d/%Y",
        amount_inverted=False,
    ),
    BankProfile(
        id="wells_fargo",
        name="Wells Fargo",
        institution_name="Wells Fargo",
        account_type="checking",
        # Wells Fargo CSVs often have no header row, but when they do:
        header_signature=["Date", "Amount", "Star", "Blank", "Description"],
        column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
        date_format="%m/%d/%Y",
        amount_inverted=False,
    ),
]

# Build a lookup by ID
PROFILES_BY_ID: dict[str, BankProfile] = {p.id: p for p in BANK_PROFILES}


def detect_bank_profile(headers: list[str], filename: str = "") -> BankProfile | None:
    """Detect which bank profile matches the given CSV headers and filename.

    Matches by checking if the CSV headers are a superset of the profile's
    header_signature. If multiple profiles match, prefer ones whose filename
    pattern also matches.
    """
    headers_set = set(h.strip() for h in headers)
    candidates: list[tuple[BankProfile, int]] = []

    for profile in BANK_PROFILES:
        sig_set = set(profile.header_signature)
        if sig_set.issubset(headers_set):
            # For very generic signatures (3 or fewer columns), require
            # a filename match to avoid false positives
            has_filename_match = (
                profile.filename_pattern
                and filename
                and re.search(profile.filename_pattern, filename)
            )
            if len(sig_set) <= 3 and not has_filename_match:
                continue

            score = len(sig_set)  # more specific signatures score higher
            if has_filename_match:
                score += 100
            candidates.append((profile, score))

    if not candidates:
        return None

    # Return the highest-scoring match
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def list_bank_profiles() -> list[dict]:
    """Return a list of supported bank profiles for the API."""
    seen = set()
    result = []
    for p in BANK_PROFILES:
        if p.id in seen:
            continue
        seen.add(p.id)
        result.append({
            "id": p.id,
            "name": p.name,
            "institution_name": p.institution_name,
            "account_type": p.account_type,
        })
    return result
