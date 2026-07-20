from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from staff.models import StaffProfile
from organisation.models import Branch


class SalaryStructure(BaseModel):
    class PayFrequency(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        BIWEEKLY = "BIWEEKLY", "Bi-Weekly"
        MONTHLY = "MONTHLY", "Monthly"

    name = models.CharField(max_length=100)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="salary_structures")
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pay_frequency = models.CharField(max_length=20, choices=PayFrequency.choices, default=PayFrequency.MONTHLY)
    effective_from = models.DateField()
    effective_until = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-effective_from"]

    def __str__(self):
        return f"{self.staff.employee_id} - {self.name} ({self.base_salary})"


class AllowanceType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DeductionType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PayrollPeriod(BaseModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PROCESSING = "PROCESSING", "Processing"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="payroll_periods")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class Payslip(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        PAID = "PAID", "Paid"

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="payslips")
    period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT, related_name="payslips")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    base_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-period__start_date"]
        constraints = [models.UniqueConstraint(fields=["staff", "period"], name="unique_payslip_per_staff_period")]

    def __str__(self):
        return f"Payslip {self.staff.employee_id} - {self.period.name}"


class PayslipAllowance(BaseModel):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name="allowances")
    allowance_type = models.ForeignKey(AllowanceType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.allowance_type.name}: {self.amount}"


class PayslipDeduction(BaseModel):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name="deductions")
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.deduction_type.name}: {self.amount}"


class LeaveType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.staff.employee_id} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    @property
    def days_count(self):
        return (self.end_date - self.start_date).days + 1


class LeaveBalance(BaseModel):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    year = models.PositiveIntegerField()
    total_days = models.PositiveIntegerField(default=0)
    used_days = models.PositiveIntegerField(default=0)
    pending_days = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["staff", "leave_type", "year"], name="unique_leave_balance")]

    @property
    def remaining_days(self):
        return self.total_days - self.used_days - self.pending_days

    def __str__(self):
        return f"{self.staff.employee_id} - {self.leave_type.name} {self.year}"
