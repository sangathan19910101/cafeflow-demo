from django.contrib import admin
from .models import (SalaryStructure, AllowanceType, DeductionType, PayrollPeriod,
                     Payslip, PayslipAllowance, PayslipDeduction, LeaveType, LeaveRequest, LeaveBalance)


class PayslipAllowanceInline(admin.TabularInline):
    model = PayslipAllowance
    extra = 0


class PayslipDeductionInline(admin.TabularInline):
    model = PayslipDeduction
    extra = 0


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("staff", "name", "base_salary", "pay_frequency", "is_active")
    list_filter = ("is_active", "pay_frequency")


@admin.register(AllowanceType)
class AllowanceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_taxable", "is_active")


@admin.register(DeductionType)
class DeductionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_mandatory", "is_active")


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "start_date", "end_date", "status")
    list_filter = ("status", "branch")


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ("staff", "period", "base_pay", "net_pay", "status", "paid_at")
    list_filter = ("status",)
    inlines = (PayslipAllowanceInline, PayslipDeductionInline)


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "days_per_year", "is_paid", "requires_approval")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "start_date", "end_date", "status")
    list_filter = ("status", "leave_type")
    date_hierarchy = "start_date"


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "year", "total_days", "used_days", "remaining_days")
    list_filter = ("year",)
