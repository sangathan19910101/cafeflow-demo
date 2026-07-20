from django.contrib import admin
from .models import ExpenseCategory, Expense, CashRegister, CashMovement, DayEndSummary
from organisation.models import TableSession


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ("table", "status", "opened_at", "closed_at", "total_amount", "is_billed")
    list_filter = ("status", "is_billed")


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "branch", "amount", "expense_date", "recorded_by")
    list_filter = ("category", "branch", "expense_date")


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "opening_balance", "closing_balance", "status", "opened_at")
    list_filter = ("status", "branch")


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ("register", "movement_type", "amount", "created_at")
    list_filter = ("movement_type",)


@admin.register(DayEndSummary)
class DayEndSummaryAdmin(admin.ModelAdmin):
    list_display = ("branch", "summary_date", "total_sales", "net_revenue", "is_closed")
    list_filter = ("is_closed", "branch")
