"""Tax summary export — generates CSV and structured data for tax filing."""

import csv
import io
import logging
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger(__name__)


def generate_tax_summary(user, tax_year: int) -> dict:
    """Generate a comprehensive tax summary for export.

    Returns structured data suitable for CSV export or display.
    """
    from taxes.models import TaxYear
    from taxes.tax_engine import calculate_taxes

    try:
        ty = TaxYear.objects.get(user=user, year=tax_year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {tax_year}."}

    docs = list(ty.documents.all())
    deductions = list(ty.deductions.all())

    # Income summary by document type
    income_by_type = defaultdict(lambda: {"total": Decimal("0"), "items": []})
    for doc in docs:
        income_by_type[doc.get_document_type_display()]["total"] += doc.amount
        income_by_type[doc.get_document_type_display()]["items"].append({
            "issuer": doc.issuer,
            "amount": str(doc.amount),
        })

    # Deductions summary by type
    deductions_by_type = defaultdict(lambda: {"total": Decimal("0"), "items": []})
    for ded in deductions:
        deductions_by_type[ded.get_deduction_type_display()]["total"] += ded.amount
        deductions_by_type[ded.get_deduction_type_display()]["items"].append({
            "description": ded.description,
            "amount": str(ded.amount),
            "is_verified": ded.is_verified,
        })

    # Calculate taxes
    from chat.tools import _build_tax_input, _serialize_tax_breakdown
    tax_input = _build_tax_input(ty)
    tax_result = calculate_taxes(tax_input)

    total_income = sum(doc.amount for doc in docs)
    total_deductions = sum(ded.amount for ded in deductions)

    return {
        "tax_year": tax_year,
        "filing_status": ty.get_filing_status_display(),
        "income_summary": {
            cat: {"total": str(data["total"]), "items": data["items"]}
            for cat, data in income_by_type.items()
        },
        "deductions_summary": {
            cat: {"total": str(data["total"]), "items": data["items"]}
            for cat, data in deductions_by_type.items()
        },
        "total_income": str(total_income),
        "total_deductions": str(total_deductions),
        "tax_breakdown": _serialize_tax_breakdown(tax_result),
        "document_count": len(docs),
        "deduction_count": len(deductions),
        "component_type": "tax_summary_export",
    }


def export_tax_csv(user, tax_year: int) -> str:
    """Generate a CSV string of the tax summary."""
    from taxes.models import TaxYear

    try:
        ty = TaxYear.objects.get(user=user, year=tax_year)
    except TaxYear.DoesNotExist:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([f"Tax Summary — {tax_year}"])
    writer.writerow([f"Filing Status: {ty.get_filing_status_display()}"])
    writer.writerow([])

    # Income Documents
    writer.writerow(["INCOME DOCUMENTS"])
    writer.writerow(["Type", "Issuer", "Amount"])
    for doc in ty.documents.all():
        writer.writerow([
            doc.get_document_type_display(),
            doc.issuer,
            f"${doc.amount:,.2f}",
        ])
    writer.writerow([])

    # Deductions
    writer.writerow(["DEDUCTIONS"])
    writer.writerow(["Type", "Description", "Amount", "Verified"])
    for ded in ty.deductions.all():
        writer.writerow([
            ded.get_deduction_type_display(),
            ded.description,
            f"${ded.amount:,.2f}",
            "Yes" if ded.is_verified else "No",
        ])
    writer.writerow([])

    # Tax Calculation
    from chat.tools import _build_tax_input
    from taxes.tax_engine import calculate_taxes

    tax_input = _build_tax_input(ty)
    result = calculate_taxes(tax_input)

    writer.writerow(["TAX CALCULATION"])
    writer.writerow(["Gross Income", f"${result.gross_income:,.2f}"])
    writer.writerow(["Adjusted Gross Income", f"${result.agi:,.2f}"])
    writer.writerow(["Deduction Used", result.deduction_used.title()])
    writer.writerow(["Taxable Income", f"${result.taxable_income:,.2f}"])
    writer.writerow(["Ordinary Tax", f"${result.ordinary_tax:,.2f}"])
    writer.writerow(["LTCG Tax", f"${result.ltcg_tax:,.2f}"])
    writer.writerow(["Self-Employment Tax", f"${result.self_employment_tax:,.2f}"])
    writer.writerow(["Total Tax", f"${result.total_tax:,.2f}"])
    writer.writerow(["Total Withheld", f"${result.total_withheld:,.2f}"])
    writer.writerow(["Amount Owed/Refund", f"${result.amount_owed:,.2f}"])
    writer.writerow(["Effective Rate", f"{result.effective_rate}%"])

    return output.getvalue()
