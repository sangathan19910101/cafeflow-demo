from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from organisation.models import Branch


class Department(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="departments", null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StaffProfile(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        TERMINATED = "TERMINATED", "Terminated"
        SUSPENDED = "SUSPENDED", "Suspended"

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="staff_profile")
    employee_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="members", null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="staff")
    designation = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    hire_date = models.DateField()
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monthly salary in NPR")
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    is_full_time = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo = models.ImageField(upload_to="staff/photos/", blank=True)

    class Meta:
        ordering = ["employee_id"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class ShiftTemplate(BaseModel):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="shift_templates")
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.PositiveIntegerField(default=0)
    requires_cashier = models.BooleanField(default=False)
    requires_waiter = models.BooleanField(default=False)
    requires_kitchen = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class ShiftAssignment(BaseModel):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="shifts")
    template = models.ForeignKey(ShiftTemplate, on_delete=models.PROTECT, related_name="assignments")
    date = models.DateField()
    notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "template__start_time"]
        constraints = [
            models.UniqueConstraint(fields=["staff", "date", "template"], name="unique_shift_per_staff_per_day")
        ]

    def __str__(self):
        return f"{self.staff.employee_id} - {self.date} {self.template.name}"


class TimeEntry(BaseModel):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="time_entries")
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(blank=True, null=True)
    break_start = models.DateTimeField(blank=True, null=True)
    break_end = models.DateTimeField(blank=True, null=True)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-clock_in"]
        verbose_name_plural = "Time Entries"

    def __str__(self):
        return f"{self.staff.employee_id} - {self.clock_in.date()}"
