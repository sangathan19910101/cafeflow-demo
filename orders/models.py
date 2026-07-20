from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import BaseModel
from organisation.models import TableSession
from menu.models import MenuItem, Modifier
from crm.models import Customer


class Order(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class OrderType(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine In"
        TAKEAWAY = "TAKEAWAY", "Takeaway"
        DELIVERY = "DELIVERY", "Delivery"

    order_number = models.CharField(max_length=20, blank=True)
    session = models.ForeignKey(TableSession, on_delete=models.PROTECT, related_name="orders", null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    customer_note = models.TextField(blank=True)
    void_reason = models.TextField(blank=True)
    discount_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            prefix = self.order_type[:3] if self.order_type else "ORD"
            date_part = timezone.now().strftime("%y%m%d")
            last_today = Order.objects.filter(order_number__startswith=f"{prefix}-{date_part}").count()
            self.order_number = f"{prefix}-{date_part}-{last_today + 1:04d}"
            while Order.objects.filter(order_number=self.order_number).exists():
                last_today += 1
                self.order_number = f"{prefix}-{date_part}-{last_today + 1:04d}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.session and self.session.status == TableSession.Status.CLOSED and self.status in [self.Status.DRAFT, self.Status.SUBMITTED]:
            raise ValidationError("Order cannot remain active in a closed session.")

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    @property
    def line_total(self):
        total = self.quantity * self.price_snapshot
        for mod in self.modifiers.all():
            total += mod.price_adjustment * self.quantity
        return total

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"


class OrderItemModifier(BaseModel):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="modifiers")
    modifier = models.ForeignKey(Modifier, on_delete=models.PROTECT)
    modifier_name = models.CharField(max_length=100)
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.modifier_name} (+{self.price_adjustment})"
