from django.contrib import admin
from .models import Reservation, WaitlistEntry


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer", "branch", "reservation_date", "reservation_time", "guest_count", "status")
    list_filter = ("status", "branch", "reservation_date")
    search_fields = ("customer__name", "customer__phone")


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ("customer", "branch", "guest_count", "status", "estimated_wait_minutes", "created_at")
    list_filter = ("status", "branch")
