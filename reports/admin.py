from django.contrib import admin
from .models import ReportTemplate, ScheduledReport, ReportExport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "default_format", "is_system", "is_active")
    list_filter = ("category", "is_active")


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ("name", "report", "frequency", "is_active", "last_sent_at")
    list_filter = ("frequency", "is_active")


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ("report", "format", "generated_by", "row_count", "generated_at")
    list_filter = ("format",)
