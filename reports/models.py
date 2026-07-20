from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel


class ReportTemplate(BaseModel):
    class Category(models.TextChoices):
        SALES = "SALES", "Sales"
        INVENTORY = "INVENTORY", "Inventory"
        STAFF = "STAFF", "Staff"
        FINANCIAL = "FINANCIAL", "Financial"
        CUSTOMER = "CUSTOMER", "Customer"
        OPERATIONS = "OPERATIONS", "Operations"

    class Format(models.TextChoices):
        PDF = "PDF", "PDF"
        CSV = "CSV", "CSV"
        EXCEL = "EXCEL", "Excel"
        HTML = "HTML", "HTML"

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField(blank=True)
    query_config = models.JSONField(default=dict, help_text="Report query parameters as JSON")
    default_format = models.CharField(max_length=10, choices=Format.choices, default=Format.CSV)
    is_system = models.BooleanField(default=False, help_text="Pre-installed report")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"[{self.category}] {self.name}"


class ScheduledReport(BaseModel):
    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"

    report = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name="schedules")
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    recipients = models.JSONField(default=list, help_text="List of email addresses")
    format = models.CharField(max_length=10, choices=ReportTemplate.Format.choices, default=ReportTemplate.Format.CSV)
    is_active = models.BooleanField(default=True)
    last_sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.frequency})"


class ReportExport(BaseModel):
    report = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name="exports")
    generated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    format = models.CharField(max_length=10, choices=ReportTemplate.Format.choices)
    file = models.FileField(upload_to="reports/exports/", blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.report.name} ({self.format}) - {self.generated_at}"
