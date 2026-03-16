"""Tax year expense report generator.

Produces audit-ready reports showing every deduction with line-item detail,
organized by TurboTax category, with totals matching TurboTax entries.
Matches the format of 2025/2025_tax_expense_report.txt.
"""

import csv
import io
from collections import defaultdict
from decimal import Decimal

from transactions.business_categorizer import categorize_for_schedule_c
from taxes.turbotax_mapping import map_to_turbotax


def generate_expense_report(user, tax_year: int, fmt: str = "json") -> dict | str:
    """Generate a detailed expense report for a tax year.

    Args:
        user: Django user instance.
        tax_year: The tax year (e.g., 2025).
        fmt: Output format — "json", "csv", or "text".

    Returns:
        dict (for JSON) or str (for CSV/text).
    """
    from imports.models import ImportBatch
    from taxes.models import TaxYear
    from transactions.models import Transaction

    try:
        ty = TaxYear.objects.get(user=user, year=tax_year)
    except TaxYear.DoesNotExist:
        if fmt == "json":
            return {"error": f"No tax year found for {tax_year}."}
        return f"Error: No tax year found for {tax_year}."

    # Gather all expense transactions for the year
    transactions = list(
        Transaction.objects.filter(
            user=user,
            transaction_type="expense",
            date__year=tax_year,
        ).select_related("category", "account").order_by("date")
    )

    # Categorize and group by TurboTax category
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
            "account": txn.account.name if txn.account else "Unknown",
            "tax_category": tax_cat,
        })

    # Apply 50% meals
    if "Meals" in categories:
        meals = categories["Meals"]
        meals["full_amount"] = meals["amount"]
        meals["amount"] = meals["amount"] / 2

    total_expenses = sum(data["amount"] for data in categories.values())

    # Data sources
    batch_sources = list(
        ImportBatch.objects.filter(
            user=user,
            status="completed",
        ).values_list("file_name", "source_institution", "imported_count")
    )

    data_sources = []
    for fname, institution, count in batch_sources:
        label = institution or fname
        data_sources.append(f"{label} ({count} transactions)")

    report_data = {
        "tax_year": tax_year,
        "filing_status": ty.get_filing_status_display(),
        "categories": {},
        "total_expenses": str(total_expenses),
        "data_sources": data_sources,
        "transaction_count": len(transactions),
        "component_type": "expense_report",
    }

    for cat in sorted(categories):
        data = categories[cat]
        entry = {
            "amount": str(data["amount"]),
            "item_count": len(data["items"]),
            "items": data["items"],
        }
        if "full_amount" in data:
            entry["full_amount"] = str(data["full_amount"])
        report_data["categories"][cat] = entry

    if fmt == "json":
        return report_data

    if fmt == "csv":
        return _format_csv(report_data)

    return _format_text(report_data)


def _format_csv(data: dict) -> str:
    """Format expense report as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([f"Tax Year {data['tax_year']} — Expense Report"])
    writer.writerow([f"Filing Status: {data['filing_status']}"])
    writer.writerow([])

    writer.writerow(["TurboTax Category", "Amount", "Item Count", "Notes"])
    for cat, info in data["categories"].items():
        notes = ""
        if "full_amount" in info:
            notes = f"Full amount: ${info['full_amount']} (50% meals limit applied)"
        writer.writerow([cat, f"${info['amount']}", info["item_count"], notes])
    writer.writerow([])
    writer.writerow(["TOTAL EXPENSES", f"${data['total_expenses']}"])
    writer.writerow([])

    writer.writerow(["DETAIL"])
    writer.writerow(["Date", "Description", "Amount", "Account", "Tax Category", "TurboTax Category"])
    for cat, info in data["categories"].items():
        for item in info["items"]:
            writer.writerow([
                item["date"],
                item["description"],
                f"${item['amount']}",
                item.get("account", ""),
                item.get("tax_category", ""),
                cat,
            ])

    writer.writerow([])
    writer.writerow(["DATA SOURCES"])
    for src in data.get("data_sources", []):
        writer.writerow([src])

    return output.getvalue()


def _format_text(data: dict) -> str:
    """Format expense report as plain text matching 2025 report format."""
    lines = []
    sep = "=" * 80

    lines.append(sep)
    lines.append(f"    {data['tax_year']} TAX YEAR — EXPENSE REPORT")
    lines.append(f"    Filing Status: {data['filing_status']}")
    lines.append(sep)
    lines.append("")

    lines.append("SCHEDULE C EXPENSES — AS ENTERED IN TURBOTAX")
    lines.append(sep)
    lines.append("")
    lines.append(f"{'Category':<40} {'Amount':>12}    Notes")
    lines.append("-" * 80)

    for cat, info in data["categories"].items():
        amount = info["amount"]
        notes = ""
        if "full_amount" in info:
            notes = f"(full: ${info['full_amount']}, 50% limit)"
        lines.append(f"{cat:<40} ${amount:>10}    {notes}")

    lines.append("-" * 80)
    lines.append(f"{'TOTAL EXPENSES':<40} ${data['total_expenses']:>10}")
    lines.append(sep)
    lines.append("")

    # Detail breakdown per category
    for cat, info in data["categories"].items():
        if info["item_count"] == 0:
            continue
        lines.append(f"{cat} — ${info['amount']} ({info['item_count']} items)")
        lines.append("-" * 60)
        for item in info["items"]:
            desc = item["description"][:50]
            lines.append(f"  {item['date']}  {desc:<50}  ${item['amount']:>10}")
        lines.append("")

    # Data sources
    lines.append(sep)
    lines.append("DATA SOURCES")
    lines.append(sep)
    for src in data.get("data_sources", []):
        lines.append(f"  - {src}")
    lines.append("")
    lines.append(sep)
    lines.append("END OF REPORT")
    lines.append(sep)

    return "\n".join(lines)
