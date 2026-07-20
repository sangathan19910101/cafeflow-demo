from django.contrib import admin
from .models import (Supplier, SupplierContact, SupplierPricing, PurchaseOrder,
                     PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


class GoodsReceiptItemInline(admin.TabularInline):
    model = GoodsReceiptItem
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "phone", "status")
    list_filter = ("status",)
    search_fields = ("name", "company", "phone")


@admin.register(SupplierContact)
class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier", "designation", "phone", "is_primary")
    list_filter = ("is_primary",)


@admin.register(SupplierPricing)
class SupplierPricingAdmin(admin.ModelAdmin):
    list_display = ("supplier", "item", "unit_price", "minimum_order_qty", "is_preferred")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "branch", "status", "order_date", "grand_total")
    list_filter = ("status", "branch")
    inlines = (PurchaseOrderItemInline,)


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "received_date", "received_by")
    inlines = (GoodsReceiptItemInline,)


@admin.register(GoodsReceiptItem)
class GoodsReceiptItemAdmin(admin.ModelAdmin):
    list_display = ("goods_receipt", "po_item", "quantity_received", "unit_price")
