from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class TaxYear(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tax_years")
    year = models.PositiveIntegerField()
    FILING_STATUS_CHOICES = [
        ("single", "Single"),
        ("married_joint", "Married Filing Jointly"),
        ("married_separate", "Married Filing Separately"),
        ("head_of_household", "Head of Household"),
    ]

    filing_status = models.CharField(max_length=30, choices=FILING_STATUS_CHOICES, default="single")
    federal_tax_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    state_tax_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year"]
        constraints = [
            models.UniqueConstraint(fields=["user", "year"], name="unique_user_tax_year"),
        ]

    def __str__(self):
        return f"{self.year} - {self.get_filing_status_display()}"


class TaxDocument(models.Model):
    DOC_TYPES = [
        ("w2", "W-2"),
        ("1099_int", "1099-INT"),
        ("1099_div", "1099-DIV"),
        ("1099_b", "1099-B"),
        ("1099_misc", "1099-MISC"),
        ("1099_nec", "1099-NEC"),
        ("1099_da", "1099-DA"),
        ("1098", "1098"),
        ("k1", "K-1"),
        ("other", "Other"),
    ]

    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=20, choices=DOC_TYPES)
    issuer = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    details = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document_type"]

    def __str__(self):
        return f"{self.get_document_type_display()} from {self.issuer}"


class DeductibleExpense(models.Model):
    DEDUCTION_TYPES = [
        ("standard", "Standard Deduction"),
        ("mortgage_interest", "Mortgage Interest"),
        ("state_local_tax", "State & Local Tax"),
        ("charitable", "Charitable Donations"),
        ("medical", "Medical Expenses"),
        ("business", "Business Expenses"),
        ("education", "Education"),
        ("home_office", "Home Office"),
        ("vehicle", "Vehicle"),
        ("insurance", "Insurance"),
        ("retirement", "Retirement Contributions"),
        ("other", "Other"),
    ]

    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name="deductions")
    receipt = models.ForeignKey("Receipt", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    deduction_type = models.CharField(max_length=30, choices=DEDUCTION_TYPES)
    turbotax_category = models.CharField(max_length=100, blank=True, help_text="TurboTax category grouping")
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        return f"{self.get_deduction_type_display()}: {self.amount}"


class Receipt(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    CATEGORY_CHOICES = [
        ("food", "Food & Dining"),
        ("groceries", "Groceries"),
        ("transportation", "Transportation"),
        ("gas", "Gas & Fuel"),
        ("shopping", "Shopping"),
        ("entertainment", "Entertainment"),
        ("health", "Health & Medical"),
        ("home", "Home & Garden"),
        ("office", "Office Supplies"),
        ("travel", "Travel"),
        ("utilities", "Utilities"),
        ("business", "Business"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receipts")
    image = models.FileField(
        upload_to="receipts/%Y/%m/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp", "pdf"])],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # OCR-extracted fields
    merchant = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tip_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, blank=True)
    raw_ocr_data = models.JSONField(default=dict, blank=True)

    # Optional links
    transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="receipts"
    )
    deductible_expense = models.ForeignKey(
        DeductibleExpense, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipt_links"
    )
    tax_year = models.ForeignKey(TaxYear, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipts")

    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Receipt {self.id}: {self.merchant or 'Unknown'} - {self.total_amount or '?'}"


class ReceiptLineItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="line_items")
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description}: {self.total_price}"
