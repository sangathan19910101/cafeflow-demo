from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import TimeEntry, StaffProfile, ShiftAssignment


class StaffService:
    @staticmethod
    @transaction.atomic
    def clock_in(staff_id):
        staff = StaffProfile.objects.get(pk=staff_id)
        if staff.status != StaffProfile.Status.ACTIVE:
            raise ValueError("Staff member is not active.")
        open_entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).exists()
        if open_entry:
            raise ValueError("Staff member already clocked in.")
        return TimeEntry.objects.create(staff=staff, clock_in=timezone.now())

    @staticmethod
    @transaction.atomic
    def clock_out(staff_id):
        staff = StaffProfile.objects.get(pk=staff_id)
        entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).select_for_update().last()
        if not entry:
            raise ValueError("No open time entry found.")
        now = timezone.now()
        entry.clock_out = now
        delta = (now - entry.clock_in).total_seconds() / 3600
        entry.total_hours = round(delta, 2)
        if entry.total_hours > 8:
            entry.overtime_hours = round(entry.total_hours - 8, 2)
        entry.save(update_fields=["clock_out", "total_hours", "overtime_hours"])
        return entry

    @staticmethod
    def get_today_shifts(branch_id):
        today = timezone.now().date()
        return ShiftAssignment.objects.filter(
            date=today, template__branch_id=branch_id
        ).select_related("staff", "template")
