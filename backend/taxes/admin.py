from django.contrib import admin

from .models import DeductibleExpense, TaxDocument, TaxYear


@admin.register(TaxYear)
class TaxYearAdmin(admin.ModelAdmin):
    list_display = ["user", "year", "filing_status", "federal_tax_paid", "state_tax_paid"]
    list_filter = ["year", "filing_status"]
    search_fields = ["user__username", "year"]


@admin.register(TaxDocument)
class TaxDocumentAdmin(admin.ModelAdmin):
    list_display = ["tax_year", "document_type", "issuer", "amount"]
    list_filter = ["document_type"]
    search_fields = ["issuer"]


@admin.register(DeductibleExpense)
class DeductibleExpenseAdmin(admin.ModelAdmin):
    list_display = ["tax_year", "deduction_type", "description", "amount", "is_verified"]
    list_filter = ["deduction_type", "is_verified"]
    search_fields = ["description"]
