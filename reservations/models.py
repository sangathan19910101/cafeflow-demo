from django.db import models
from core.models import BaseModel
from organisation.models import Branch, Table
from crm.models import Customer


class Reservation(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SEATED = "SEATED", "Seated"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"
        COMPLETED = "COMPLETED", "Completed"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="reservations")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="reservations")
    tables = models.ManyToManyField(Table, blank=True, related_name="reservations")
    guest_count = models.PositiveIntegerField()
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=120)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    special_requests = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    seated_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_paid = models.BooleanField(default=False)
    is_walk_in = models.BooleanField(default=False)
    source = models.CharField(max_length=50, blank=True, help_text="phone, website, walk-in, third-party")

    class Meta:
        ordering = ["reservation_date", "reservation_time"]

    def __str__(self):
        return f"{self.customer.name} - {self.reservation_date} {self.reservation_time}"


class WaitlistEntry(BaseModel):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        NOTIFIED = "NOTIFIED", "Notified"
        SEATED = "SEATED", "Seated"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="waitlist_entries")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="waitlist")
    guest_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    notified_at = models.DateTimeField(blank=True, null=True)
    seated_at = models.DateTimeField(blank=True, null=True)
    estimated_wait_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Waitlist Entries"

    def __str__(self):
        return f"{self.customer.name} ({self.guest_count} guests) - {self.status}"
