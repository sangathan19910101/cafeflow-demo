from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel
from organisation.models import TableSession, Branch
from crm.models import Customer


class Bill(BaseModel):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIAL", "Partially Paid"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"
        REFUNDED = "REFUNDED", "Refunded"

    class SaleType(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine In"
        TAKEAWAY = "TAKEAWAY", "Takeaway"
        DELIVERY = "DELIVERY", "Delivery"
        QUICK_SALE = "QUICK_SALE", "Quick Sale"

    bill_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    session = models.OneToOneField(TableSession, on_delete=models.PROTECT, related_name="bill", null=True, blank=True)
    sale_type = models.CharField(max_length=20, choices=SaleType.choices, default=SaleType.DINE_IN)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="bills", null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="bills")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rounding_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(blank=True, null=True)
    void_reason = models.TextField(blank=True)
    voided_at = models.DateTimeField(blank=True, null=True)
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-generated_at"]

    def save(self, *args, **kwargs):
        if not self.bill_number:
            date_part = timezone.now().strftime("%y%m%d")
            last_today = Bill.objects.filter(bill_number__startswith=f"B-{date_part}").count()
            self.bill_number = f"B-{date_part}-{last_today + 1:04d}"
            while Bill.objects.filter(bill_number=self.bill_number).exists():
                last_today += 1
                self.bill_number = f"B-{date_part}-{last_today + 1:04d}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.grand_total < 0:
            raise ValidationError("Grand total cannot be negative.")

    @property
    def total_paid(self):
        return self.payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0

    @property
    def balance_due(self):
        return max(self.grand_total - self.total_paid, 0)

    @property
    def is_fully_paid(self):
        return self.total_paid >= self.grand_total

    def __str__(self):
        return f"Bill {self.bill_number}"


class Payment(BaseModel):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        QR = "QR", "QR"
        UPI = "UPI", "UPI"
        ESEWA = "ESEWA", "eSewa"
        KHALTI = "KHALTI", "Khalti"
        FONEPAY = "FONEPAY", "FonePay"
        SPLIT = "SPLIT", "Split Payment"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name="payments")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    transaction_id = models.CharField(max_length=200, blank=True)
    gateway = models.CharField(max_length=50, blank=True, help_text="Payment gateway used")
    card_last_four = models.CharField(max_length=4, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=100, blank=True)
    is_refunded = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.payment_method} Rs.{self.amount_paid} - {self.status}"


class QuickSaleItem(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="quick_items")
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"
