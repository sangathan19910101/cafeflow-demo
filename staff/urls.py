from django.urls import path
from .views import (
    staff_list, staff_detail, shift_calendar, time_clock,
    create_staff, edit_staff, create_shift_template,
    assign_shift, bulk_assign_shifts,
    clock_in, clock_out, edit_time_entry,
    monthly_payout, attendance_report,
)

urlpatterns = [
    path("create/", create_staff, name="create_staff"),
    path("", staff_list, name="staff_list"),
    path("monthly-payout/", monthly_payout, name="monthly_payout"),
    path("attendance/", attendance_report, name="attendance_report"),
    path("shifts/create/", create_shift_template, name="create_shift"),
    path("shifts/assign/", assign_shift, name="assign_shift"),
    path("shifts/bulk-assign/", bulk_assign_shifts, name="bulk_assign_shifts"),
    path("shifts/calendar/", shift_calendar, name="shift_calendar"),
    path("time-clock/", time_clock, name="time_clock"),
    path("time-clock/in/", clock_in, name="clock_in"),
    path("time-clock/out/<uuid:entry_id>/", clock_out, name="clock_out"),
    path("time-clock/<uuid:entry_id>/edit/", edit_time_entry, name="edit_time_entry"),
    path("<uuid:staff_id>/edit/", edit_staff, name="edit_staff"),
    path("<uuid:staff_id>/", staff_detail, name="staff_detail"),
]
