"""TurboTax category mapping for Schedule C expenses.

Maps between IRS Schedule C line items, nullbook tax categories,
and the category groupings that TurboTax uses in its interview flow.
"""

from collections import defaultdict
from decimal import Decimal

# TurboTax uses these grouping names in its Schedule C interview
TURBOTAX_CATEGORIES = {
    "Vehicle": {
        "schedule_c_lines": ["car_truck"],
        "notes": "Mileage or actual expenses. TurboTax asks for odometer readings.",
    },
    "Communications": {
        "schedule_c_lines": ["utilities"],
        "notes": "Phone and internet bills. Enter business-use percentage.",
    },
    "Assets": {
        "schedule_c_lines": ["depreciation"],
        "notes": "Equipment, computers, phones over $2,500. Section 179 or depreciation.",
    },
    "Advertising": {
        "schedule_c_lines": ["advertising"],
        "notes": "Marketing, promotion, business development.",
    },
    "Meals": {
        "schedule_c_lines": ["meals"],
        "notes": "Business meals. TurboTax automatically applies 50% limit.",
    },
    "Business travel": {
        "schedule_c_lines": ["travel"],
        "notes": "Airfare, hotels, transport for business trips.",
    },
    "Office expenses": {
        "schedule_c_lines": ["office_expense"],
        "notes": "Software subscriptions, office supplies, postage.",
    },
    "Taxes and licenses": {
        "schedule_c_lines": ["taxes_licenses"],
        "notes": "Business licenses, franchise taxes, state filing fees.",
    },
    "Insurance": {
        "schedule_c_lines": ["insurance"],
        "notes": "Business insurance premiums (not health insurance).",
    },
    "Legal and professional services": {
        "schedule_c_lines": ["legal_professional"],
        "notes": "Attorney, CPA, accountant, tax prep fees.",
    },
    "Contract labor": {
        "schedule_c_lines": ["contract_labor"],
        "notes": "Payments to independent contractors.",
    },
    "Rent or lease": {
        "schedule_c_lines": ["rent_lease_property", "rent_lease_vehicle"],
        "notes": "Office rent, co-working space, equipment leases.",
    },
    "Repairs and maintenance": {
        "schedule_c_lines": ["repairs_maintenance"],
        "notes": "Equipment repairs, maintenance costs.",
    },
    "Supplies": {
        "schedule_c_lines": ["supplies"],
        "notes": "Materials and supplies consumed in business.",
    },
    "Other miscellaneous expenses": {
        "schedule_c_lines": ["other", "commissions", "interest_mortgage",
                             "interest_other", "wages"],
        "notes": "Anything that doesn't fit the categories above.",
    },
}

# Map nullbook / process_expenses.py tax categories → TurboTax categories
CATEGORY_TO_TURBOTAX = {
    # Travel subtypes
    "Travel - Airfare": "Business travel",
    "Travel - Lodging": "Business travel",
    "Travel - Transport": "Business travel",
    "Travel - Parking": "Vehicle",
    "Travel - Gas/Fuel": "Vehicle",
    "Travel - Other": "Business travel",

    # Meals
    "Meals & Entertainment": "Meals",

    # Software
    "Software & SaaS": "Other miscellaneous expenses",

    # Communications
    "Internet & Phone": "Communications",

    # Equipment
    "Equipment & Supplies": "Assets",

    # Education
    "Education & Subscriptions": "Other miscellaneous expenses",

    # Marketing
    "Advertising & Marketing": "Advertising",
    "Business Promotion - Fly Fishing App": "Advertising",

    # Insurance
    "Insurance": "Insurance",

    # Professional services
    "Professional Services": "Legal and professional services",

    # Schedule C category mappings
    "advertising": "Advertising",
    "car_truck": "Vehicle",
    "commissions": "Other miscellaneous expenses",
    "contract_labor": "Contract labor",
    "depreciation": "Assets",
    "insurance": "Insurance",
    "interest_mortgage": "Other miscellaneous expenses",
    "interest_other": "Other miscellaneous expenses",
    "legal_professional": "Legal and professional services",
    "office_expense": "Office expenses",
    "rent_lease_vehicle": "Rent or lease",
    "rent_lease_property": "Rent or lease",
    "repairs_maintenance": "Repairs and maintenance",
    "supplies": "Supplies",
    "taxes_licenses": "Taxes and licenses",
    "travel": "Business travel",
    "meals": "Meals",
    "utilities": "Communications",
    "wages": "Other miscellaneous expenses",
    "other": "Other miscellaneous expenses",

    # Catch-all categories from business_categorizer
    "Bills & Utilities": "Communications",
    "Fees & Adjustments": "Other miscellaneous expenses",
    "Groceries (Review for Business Use)": "Meals",
    "Shopping (Review for Business Use)": "Other miscellaneous expenses",
    "Health & Wellness": "Other miscellaneous expenses",
    "Automotive": "Vehicle",
    "Gifts & Donations": "Other miscellaneous expenses",
}


def map_to_turbotax(category: str) -> str:
    """Map a tax category to its TurboTax equivalent."""
    return CATEGORY_TO_TURBOTAX.get(category, "Other miscellaneous expenses")


def generate_turbotax_report(user, tax_year: int) -> dict:
    """Generate an expense report grouped by TurboTax categories.

    Returns:
        {
            "tax_year": int,
            "categories": {
                "Vehicle": {"amount": "...", "items": [...]},
                ...
            },
            "total_expenses": "...",
        }
    """
    from transactions.models import Transaction
    from transactions.business_categorizer import categorize_for_schedule_c

    transactions = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__year=tax_year,
    ).select_related("category")

    categories = defaultdict(lambda: {"amount": Decimal("0"), "items": []})

    for txn in transactions:
        bank_cat = txn.category.name if txn.category else ""
        tax_cat = categorize_for_schedule_c(
            txn.description,
            bank_category=bank_cat,
            amount=-float(txn.amount),
        )

        if tax_cat in ("INCOME / PAYMENT", "Uncategorized (Review)",
                        "Personal", "Home (Personal)"):
            continue

        tt_cat = map_to_turbotax(tax_cat)
        categories[tt_cat]["amount"] += txn.amount
        categories[tt_cat]["items"].append({
            "date": str(txn.date),
            "description": txn.description,
            "amount": str(txn.amount),
            "tax_category": tax_cat,
        })

    # Apply 50% meals adjustment
    if "Meals" in categories:
        meals = categories["Meals"]
        meals["full_amount"] = str(meals["amount"])
        meals["amount"] = meals["amount"] / 2

    total = sum(data["amount"] for data in categories.values())

    formatted = {}
    for cat in sorted(categories):
        data = categories[cat]
        formatted[cat] = {
            "amount": str(data["amount"]),
            "item_count": len(data["items"]),
            "items": data["items"],
            "notes": TURBOTAX_CATEGORIES.get(cat, {}).get("notes", ""),
        }
        if "full_amount" in data:
            formatted[cat]["full_amount"] = data["full_amount"]

    return {
        "tax_year": tax_year,
        "categories": formatted,
        "total_expenses": str(total),
        "component_type": "turbotax_report",
    }
