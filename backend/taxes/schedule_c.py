"""Schedule C (Self-Employment) calculation logic.

Aggregates self-employment income and business expenses from
transactions and tax documents to generate Schedule C data.
"""

import logging
from collections import defaultdict
from decimal import Decimal

from django.db import models
from django.db.models import Sum

logger = logging.getLogger(__name__)

# IRS Schedule C expense categories
SCHEDULE_C_CATEGORIES = {
    "advertising": "Advertising",
    "car_truck": "Car and truck expenses",
    "commissions": "Commissions and fees",
    "contract_labor": "Contract labor",
    "depreciation": "Depreciation",
    "insurance": "Insurance (other than health)",
    "interest_mortgage": "Interest: Mortgage",
    "interest_other": "Interest: Other",
    "legal_professional": "Legal and professional services",
    "office_expense": "Office expense",
    "rent_lease_vehicle": "Rent or lease: Vehicles",
    "rent_lease_property": "Rent or lease: Other property",
    "repairs_maintenance": "Repairs and maintenance",
    "supplies": "Supplies",
    "taxes_licenses": "Taxes and licenses",
    "travel": "Travel",
    "meals": "Meals (50% deductible)",
    "utilities": "Utilities",
    "wages": "Wages",
    "other": "Other expenses",
}

# Map transaction categories to Schedule C categories
CATEGORY_TO_SCHEDULE_C = {
    "office supplies": "office_expense",
    "office": "office_expense",
    "software": "office_expense",
    "advertising": "advertising",
    "marketing": "advertising",
    "professional services": "legal_professional",
    "legal": "legal_professional",
    "accounting": "legal_professional",
    "insurance": "insurance",
    "travel": "travel",
    "meals": "meals",
    "food": "meals",
    "dining": "meals",
    "utilities": "utilities",
    "internet": "utilities",
    "phone": "utilities",
    "rent": "rent_lease_property",
    "gas": "car_truck",
    "auto": "car_truck",
    "parking": "car_truck",
    "repairs": "repairs_maintenance",
    "supplies": "supplies",
    "education": "other",
    "subscriptions": "other",
}


def generate_schedule_c(user, tax_year: int) -> dict:
    """Generate Schedule C data from transactions and tax documents.

    Returns:
        {
            "gross_income": Decimal,
            "expenses_by_category": {...},
            "total_expenses": Decimal,
            "net_profit": Decimal,
            "transactions_used": int,
        }
    """
    from taxes.models import TaxYear
    from transactions.models import Transaction

    try:
        ty = TaxYear.objects.get(user=user, year=tax_year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {tax_year}."}

    # Calculate gross self-employment income from 1099-NEC documents
    se_docs = ty.documents.filter(document_type="1099_nec")
    gross_income = sum(d.amount for d in se_docs)

    # Also include income from business-category income transactions
    business_income = Transaction.objects.filter(
        user=user,
        transaction_type="income",
        date__year=tax_year,
        category__name__icontains="business",
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    gross_income += business_income

    # Gather business expenses: only transactions linked to a business deduction
    # via receipts, or in categories explicitly named "business"
    from taxes.models import Receipt

    # Transaction IDs linked to business deductions via receipts
    business_txn_ids = set(
        Receipt.objects.filter(
            user=user,
            tax_year=ty,
            deductible_expense__isnull=False,
            transaction__isnull=False,
        ).values_list("transaction_id", flat=True)
    )

    # Also include transactions in explicitly business-named categories
    business_expenses = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__year=tax_year,
    ).select_related("category").filter(
        models.Q(id__in=business_txn_ids)
        | models.Q(category__name__icontains="business")
    )

    expenses_by_category = defaultdict(lambda: {"amount": Decimal("0"), "items": []})

    for txn in business_expenses:
        cat_name = (txn.category.name if txn.category else "").lower()
        schedule_c_cat = None

        for pattern, sc_cat in CATEGORY_TO_SCHEDULE_C.items():
            if pattern in cat_name:
                schedule_c_cat = sc_cat
                break

        if not schedule_c_cat:
            schedule_c_cat = "other"

        expenses_by_category[schedule_c_cat]["amount"] += txn.amount
        expenses_by_category[schedule_c_cat]["items"].append({
            "id": txn.id,
            "date": str(txn.date),
            "description": txn.description,
            "amount": str(txn.amount),
        })

    # Also include claimed business deductions
    business_deductions = ty.deductions.filter(
        deduction_type__in=["business", "home_office", "vehicle"],
    )

    for ded in business_deductions:
        sc_cat = "other"
        if ded.deduction_type == "home_office":
            sc_cat = "rent_lease_property"
        elif ded.deduction_type == "vehicle":
            sc_cat = "car_truck"

        expenses_by_category[sc_cat]["amount"] += ded.amount
        expenses_by_category[sc_cat]["items"].append({
            "description": ded.description,
            "amount": str(ded.amount),
            "source": "deduction",
        })

    # Apply meals limitation (50% deductible)
    if "meals" in expenses_by_category:
        meals_total = expenses_by_category["meals"]["amount"]
        expenses_by_category["meals"]["full_amount"] = str(meals_total)
        expenses_by_category["meals"]["amount"] = meals_total / 2

    total_deductible = sum(data["amount"] for data in expenses_by_category.values())
    net_profit = gross_income - total_deductible

    # Format for output
    formatted_expenses = {}
    for cat, data in sorted(expenses_by_category.items()):
        formatted_expenses[cat] = {
            "label": SCHEDULE_C_CATEGORIES.get(cat, cat),
            "amount": str(data["amount"]),
            "item_count": len(data["items"]),
        }

    return {
        "tax_year": tax_year,
        "gross_income": str(gross_income),
        "expenses": formatted_expenses,
        "total_expenses": str(total_deductible),
        "net_profit": str(net_profit),
        "se_tax_estimate": str(net_profit * Decimal("0.9235") * Decimal("0.153")),
        "component_type": "schedule_c",
    }
