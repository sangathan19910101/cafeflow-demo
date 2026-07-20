from django.contrib import admin
from .models import Bill, Payment, QuickSaleItem


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("paid_at",)


class QuickSaleItemInline(admin.TabularInline):
    model = QuickSaleItem
    extra = 0


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "status", "grand_total", "sale_type", "branch", "generated_at")
    list_filter = ("status", "sale_type", "branch")
    search_fields = ("bill_number",)
    inlines = (PaymentInline, QuickSaleItemInline)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("bill", "payment_method", "amount_paid", "status", "transaction_id", "paid_at")
    list_filter = ("payment_method", "status")


@admin.register(QuickSaleItem)
class QuickSaleItemAdmin(admin.ModelAdmin):
    list_display = ("bill", "item_name", "quantity", "unit_price", "line_total")
