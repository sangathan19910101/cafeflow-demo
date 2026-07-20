from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from organisation.models import Branch
from inventory.models import InventoryItem


class Supplier(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        BLACKLISTED = "BLACKLISTED", "Blacklisted"

    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=200, blank=True, help_text="e.g., Net 30")
    lead_time_days = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    branches = models.ManyToManyField(Branch, blank=True, related_name="suppliers")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierContact(BaseModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"


class SupplierPricing(BaseModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="pricing")
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="supplier_pricing")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    is_preferred = models.BooleanField(default=False)
    valid_from = models.DateField()
    valid_until = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["unit_price"]

    def __str__(self):
        return f"{self.supplier.name} - {self.item.name} @ {self.unit_price}"


class PurchaseOrder(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent to Supplier"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PARTIAL = "PARTIAL", "Partially Received"
        RECEIVED = "RECEIVED", "Fully Received"
        CANCELLED = "CANCELLED", "Cancelled"

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    ordered_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="purchase_orders")
    sent_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"PO-{self.po_number} ({self.supplier.name})"


class PurchaseOrderItem(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="po_items")
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.item.name} x {self.quantity_ordered}"


class GoodsReceipt(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="goods_receipts")
    received_date = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    reference_document = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-received_date"]
        verbose_name_plural = "Goods Receipts"

    def __str__(self):
        return f"GR for PO-{self.purchase_order.po_number} ({self.received_date.date()})"


class GoodsReceiptItem(BaseModel):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="items")
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT, related_name="receipt_items")
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.po_item.item.name} x {self.quantity_received}"


class PurchaseReturn(BaseModel):
    class ReturnReason(models.TextChoices):
        DEFECTIVE = "DEFECTIVE", "Defective"
        DAMAGED = "DAMAGED", "Damaged in Transit"
        WRONG_ITEM = "WRONG_ITEM", "Wrong Item"
        EXPIRED = "EXPIRED", "Expired"
        OVERSTOCK = "OVERSTOCK", "Overstock"
        OTHER = "OTHER", "Other"

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="returns")
    returned_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True)
    return_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=20, choices=ReturnReason.choices)
    notes = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    restocked = models.BooleanField(default=False, help_text="Has the returned item been restocked?")

    class Meta:
        ordering = ["-return_date"]

    def __str__(self):
        return f"Return for PO-{self.purchase_order.po_number} ({self.get_reason_display()})"


class PurchaseReturnItem(BaseModel):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name="items")
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason_detail = models.TextField(blank=True)

    def __str__(self):
        return f"{self.po_item.item.name} x {self.quantity}"
