from django.db import models
from core.models import BaseModel
from organisation.models import Branch
from orders.models import Order, OrderItem


class KDSStation(BaseModel):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="kds_stations")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class KDSDisplay(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        SERVED = "SERVED", "Served"

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="kds_entry")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="kds_entries")
    station = models.ForeignKey(KDSStation, on_delete=models.SET_NULL, null=True, blank=True, related_name="displays")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    display_notes = models.TextField(blank=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    priority = models.PositiveIntegerField(default=0)
    estimated_completion = models.DateTimeField(blank=True, null=True)
    is_urgent = models.BooleanField(default=False)
    alert_minutes = models.PositiveIntegerField(default=0, help_text="Alert if not started within N minutes")
    assigned_cook = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-is_urgent", "priority", "created_at"]

    def __str__(self):
        return f"KDS #{self.order.order_number} - {self.status}"


class KDSItem(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"

    kds_entry = models.ForeignKey(KDSDisplay, on_delete=models.CASCADE, related_name="kds_items")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="kds_status")
    menu_item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.menu_item_name} x{self.quantity} - {self.status}"
