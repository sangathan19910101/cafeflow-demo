from django.contrib import admin
from .models import Department, StaffProfile, ShiftTemplate, ShiftAssignment, TimeEntry


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "branch")
    list_filter = ("branch",)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user", "designation", "department", "branch", "status")
    list_filter = ("status", "department", "branch", "is_full_time")
    search_fields = ("employee_id", "user__username", "user__first_name", "user__last_name")


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "start_time", "end_time")
    list_filter = ("branch",)


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "date", "template", "is_confirmed")
    list_filter = ("is_confirmed", "date")
    date_hierarchy = "date"


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("staff", "clock_in", "clock_out", "total_hours", "is_approved")
    list_filter = ("is_approved",)
    date_hierarchy = "clock_in"
