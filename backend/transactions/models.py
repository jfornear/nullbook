from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6366f1")  # hex color

    class Meta:
        ordering = ["name"]
        unique_together = ["user", "name"]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
        ("transfer", "Transfer"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    tags = models.ManyToManyField(Tag, blank=True, related_name="transactions")
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default="expense", db_index=True)
    description = models.CharField(max_length=500)
    notes = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    import_batch = models.ForeignKey("imports.ImportBatch", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.description}: {self.amount}"


class CategoryRule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="category_rules")
    pattern = models.CharField(max_length=200, help_text="Text pattern to match in transaction description")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="rules")
    auto_generated = models.BooleanField(default=False, help_text="True if created automatically from user corrections")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pattern"]

    def __str__(self):
        return f"{self.pattern} → {self.category}"


class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ("weekly", "Weekly"),
        ("biweekly", "Bi-weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semi_annual", "Semi-annual"),
        ("annual", "Annual"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("paused", "Paused"),
        ("possibly_cancelled", "Possibly Cancelled"),
        ("cancellation_pending", "Cancellation Pending"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    merchant = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="monthly")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="subscriptions")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="active", db_index=True)
    confidence = models.FloatField(default=0.0, help_text="Detection confidence score 0-1")
    last_charged = models.DateField(null=True, blank=True)
    next_expected = models.DateField(null=True, blank=True, db_index=True)
    cancellation_url = models.URLField(blank=True)
    cancellation_method = models.CharField(max_length=50, blank=True, help_text="web, email, phone")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-amount"]
        unique_together = ["user", "merchant"]

    def __str__(self):
        return f"{self.merchant}: ${self.amount}/{self.frequency}"

    @property
    def annual_cost(self):
        multiplier = {
            "weekly": 52, "biweekly": 26, "monthly": 12,
            "quarterly": 4, "semi_annual": 2, "annual": 1,
        }
        return self.amount * multiplier.get(self.frequency, 12)


class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="goals")
    linked_account = models.ForeignKey(
        "accounts.Account", on_delete=models.SET_NULL, null=True, blank=True, related_name="goals"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-target_date", "-created_at"]

    def __str__(self):
        return f"{self.name}: ${self.current_amount}/${self.target_amount}"

    @property
    def progress_pct(self):
        if self.target_amount <= 0:
            return 0
        return min(float(self.current_amount) / float(self.target_amount) * 100, 100)


class Budget(models.Model):
    PERIOD_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("annual", "Annual"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name="budgets")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default="monthly")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-amount"]
        unique_together = ["user", "category"]

    def __str__(self):
        cat = self.category.name if self.category else "Total"
        return f"{cat}: ${self.amount}/{self.period}"
