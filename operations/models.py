from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from organisation.models import Branch


class ExpenseCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Expense(BaseModel):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    expense_date = models.DateField()
    receipt_image = models.ImageField(upload_to="expenses/receipts/", blank=True)
    recorded_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    is_reimbursable = models.BooleanField(default=False)
    reimbursed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-expense_date"]

    def __str__(self):
        return f"{self.category.name} - Rs.{self.amount} ({self.expense_date})"


class CashRegister(BaseModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="cash_registers")
    name = models.CharField(max_length=100, default="Main Register")
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    opened_at = models.DateTimeField()
    closed_at = models.DateTimeField(blank=True, null=True)
    opened_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="cash_opens")
    closed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="cash_closes")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.name} ({self.branch.name}) - {self.status}"


class CashMovement(BaseModel):
    class MovementType(models.TextChoices):
        IN = "IN", "Cash In"
        OUT = "OUT", "Cash Out"
        PAYMENT = "PAYMENT", "Payment Collected"
        EXPENSE = "EXPENSE", "Expense Paid"
        TRANSFER = "TRANSFER", "Transfer"

    register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} Rs.{self.amount}"


class DayEndSummary(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="day_end_summaries")
    summary_date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_card = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_online = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    average_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-summary_date"]
        verbose_name_plural = "Day End Summaries"
        constraints = [models.UniqueConstraint(fields=["branch", "summary_date"], name="unique_daily_summary")]

    def __str__(self):
        return f"{self.branch.name} - {self.summary_date}"
