from datetime import date, timedelta, datetime
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from core.nepali_calendar import ad_to_bs, format_bs_date, get_today_bs
from core.permissions import group_required
from .models import StaffProfile, Department, ShiftTemplate, ShiftAssignment, TimeEntry
from .services import StaffService
from payroll.models import LeaveRequest


@group_required("Admin", "Manager")
def staff_list(request):
    staff = StaffProfile.objects.select_related("user", "department", "branch").all().order_by("employee_id")
    department_name = request.GET.get("department")
    status_filter = request.GET.get("status")
    if department_name:
        staff = staff.filter(department__name__icontains=department_name)
    if status_filter:
        staff = staff.filter(status=status_filter)
    return render(request, "staff/staff_list.html", {"staff": staff, "Status": StaffProfile.Status})


@group_required("Admin", "Manager")
def staff_detail(request, staff_id):
    profile = get_object_or_404(
        StaffProfile.objects.select_related("user", "department", "branch").prefetch_related("user__groups"),
        pk=staff_id,
    )
    recent_entries = TimeEntry.objects.filter(staff=profile).order_by("-clock_in")[:30]
    shifts = ShiftAssignment.objects.filter(staff=profile).select_related("template").order_by("-date")[:30]

    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    month_entries = TimeEntry.objects.filter(
        staff=profile,
        clock_in__date__gte=current_month_start,
    )
    total_hours = sum((e.total_hours or 0) for e in month_entries)
    total_overtime = sum((e.overtime_hours or 0) for e in month_entries)
    working_days = month_entries.values("clock_in__date").distinct().count()

    return render(request, "staff/staff_detail.html", {
        "profile": profile,
        "recent_entries": recent_entries,
        "shifts": shifts,
        "month_hours": total_hours,
        "month_overtime": total_overtime,
        "month_working_days": working_days,
    })


@group_required("Admin", "Manager")
def shift_calendar(request):
    branch_id = request.GET.get("branch")
    date_str = request.GET.get("date")
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    try:
        bs_date = ad_to_bs(target_date)
        bs_date_display = format_bs_date(*bs_date)
    except Exception:
        bs_date_display = str(target_date)

    prev_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)
    shifts = ShiftAssignment.objects.filter(date=target_date).select_related("staff", "staff__user", "template")
    if branch_id:
        shifts = shifts.filter(template__branch_id=branch_id)

    from organisation.models import Branch
    templates = ShiftTemplate.objects.all()
    staff_list = StaffProfile.objects.filter(status=StaffProfile.Status.ACTIVE).select_related("user")
    return render(request, "staff/shift_calendar.html", {
        "shifts": shifts,
        "templates": templates,
        "staff_list": staff_list,
        "target_date": target_date,
        "bs_date": bs_date_display,
        "prev_date": prev_date,
        "next_date": next_date,
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def assign_shift(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        template_id = request.POST.get("template")
        shift_date = request.POST.get("date")
        if staff_id and template_id and shift_date:
            try:
                ShiftAssignment.objects.get_or_create(
                    staff_id=staff_id,
                    template_id=template_id,
                    date=datetime.strptime(shift_date, "%Y-%m-%d").date(),
                )
                messages.success(request, "Shift assigned.")
            except Exception as e:
                messages.error(request, str(e))
            return redirect("shift_calendar")
        messages.error(request, "All fields required.")
    return redirect("shift_calendar")


@group_required("Admin", "Manager")
def bulk_assign_shifts(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        template_id = request.POST.get("template")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        repeat_days = request.POST.getlist("repeat_days")

        if staff_id and template_id and start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if not repeat_days:
                    repeat_days = ["0", "1", "2", "3", "4", "5", "6"]

                current = start_date
                count = 0
                while current <= end_date:
                    if str(current.weekday()) in repeat_days:
                        ShiftAssignment.objects.get_or_create(
                            staff_id=staff_id,
                            template_id=template_id,
                            date=current,
                        )
                        count += 1
                    current += timedelta(days=1)
                messages.success(request, f"Assigned {count} shifts from {start_date} to {end_date}.")
            except Exception as e:
                messages.error(request, str(e))
            return redirect("shift_calendar")
        messages.error(request, "Staff, template, start and end date required.")
    return redirect("shift_calendar")


@group_required("Admin", "Manager")
def time_clock(request):
    entries = TimeEntry.objects.select_related("staff", "staff__user").filter(
        clock_in__date=timezone.now().date()
    ).order_by("-clock_in")
    active_staff = StaffProfile.objects.filter(status=StaffProfile.Status.ACTIVE).select_related("user")
    return render(request, "staff/time_clock.html", {
        "entries": entries,
        "active_staff": active_staff,
    })


@group_required("Admin", "Manager")
def clock_in(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff_id")
        if staff_id:
            staff = get_object_or_404(StaffProfile, pk=staff_id)
            existing = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).first()
            if existing:
                messages.error(request, f"{staff.user.get_full_name()} already clocked in.")
            else:
                TimeEntry.objects.create(staff=staff, clock_in=timezone.now())
                messages.success(request, f"{staff.user.get_full_name()} clocked in.")
            return redirect("time_clock")
    return redirect("time_clock")


@group_required("Admin", "Manager")
def clock_out(request, entry_id):
    entry = get_object_or_404(TimeEntry, pk=entry_id)
    if entry.clock_out:
        messages.error(request, "Already clocked out.")
    else:
        now = timezone.now()
        entry.clock_out = now
        delta = now - entry.clock_in
        entry.total_hours = round(delta.total_seconds() / 3600, 2)
        if entry.total_hours > 8:
            entry.overtime_hours = round(entry.total_hours - 8, 2)
            entry.total_hours = 8
        entry.save(update_fields=["clock_out", "total_hours", "overtime_hours"])
        messages.success(request, "Clocked out.")
    return redirect("time_clock")


@group_required("Admin")
def edit_time_entry(request, entry_id):
    entry = get_object_or_404(TimeEntry, pk=entry_id)
    if request.method == "POST":
        from datetime import datetime
        try:
            clock_in_str = request.POST.get("clock_in")
            clock_out_str = request.POST.get("clock_out") or None
            if clock_in_str:
                entry.clock_in = timezone.make_aware(datetime.strptime(clock_in_str, "%Y-%m-%dT%H:%M"))
            if clock_out_str:
                entry.clock_out = timezone.make_aware(datetime.strptime(clock_out_str, "%Y-%m-%dT%H:%M"))
                delta = entry.clock_out - entry.clock_in
                total = round(delta.total_seconds() / 3600, 2)
                entry.total_hours = min(total, 8)
                entry.overtime_hours = max(0, round(total - 8, 2))
            else:
                entry.clock_out = None
                entry.total_hours = 0
                entry.overtime_hours = 0
            entry.total_hours = Decimal(request.POST.get("total_hours", entry.total_hours))
            entry.overtime_hours = Decimal(request.POST.get("overtime_hours", entry.overtime_hours))
            entry.is_approved = request.POST.get("is_approved") == "on"
            entry.notes = request.POST.get("notes", entry.notes)
            entry.save()
            messages.success(request, "Time entry updated.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect("time_clock")
    return render(request, "staff/edit_time_entry.html", {"entry": entry})


@group_required("Admin", "Manager")
def create_staff(request):
    from django.contrib.auth.models import User
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        employee_id = request.POST.get("employee_id")
        designation = request.POST.get("designation", "")
        branch_id = request.POST.get("branch")
        department_name = request.POST.get("department", "").strip()
        monthly_salary = request.POST.get("monthly_salary", 0)
        hourly_rate = request.POST.get("hourly_rate", 0)
        phone = request.POST.get("phone", "")
        address = request.POST.get("address", "")

        if username and password and employee_id and branch_id:
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
            )
            if department_name:
                department, _ = Department.objects.get_or_create(name=department_name)
                department_id = department.id
            else:
                department_id = None

            profile = StaffProfile.objects.create(
                user=user, employee_id=employee_id, designation=designation,
                branch_id=branch_id, department_id=department_id,
                hire_date=timezone.now().date(),
                monthly_salary=Decimal(monthly_salary or 0),
                hourly_rate=Decimal(hourly_rate or 0),
                phone=phone, address=address,
            )
            messages.success(request, f"Staff '{user.get_full_name()}' created.")
            return redirect("staff_list")
        messages.error(request, "Username, password, employee ID, and branch are required.")

    from organisation.models import Branch
    return render(request, "staff/create_staff.html", {
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def edit_staff(request, staff_id):
    profile = get_object_or_404(StaffProfile, pk=staff_id)
    if request.method == "POST":
        profile.designation = request.POST.get("designation", profile.designation)
        profile.monthly_salary = Decimal(request.POST.get("monthly_salary", profile.monthly_salary))
        profile.hourly_rate = Decimal(request.POST.get("hourly_rate", profile.hourly_rate))
        profile.phone = request.POST.get("phone", profile.phone)
        profile.address = request.POST.get("address", profile.address)
        profile.status = request.POST.get("status", profile.status)
        profile.is_full_time = request.POST.get("is_full_time") == "on"
        department_name = request.POST.get("department", "").strip()
        if department_name:
            department, _ = Department.objects.get_or_create(name=department_name)
            profile.department = department
        profile.save()
        messages.success(request, "Staff updated.")
        return redirect("staff_detail", staff_id=staff_id)

    from organisation.models import Branch
    return render(request, "staff/edit_staff.html", {
        "profile": profile,
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def create_shift_template(request):
    from organisation.models import Branch
    if request.method == "POST":
        name = request.POST.get("name")
        branch_id = request.POST.get("branch")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        break_minutes = request.POST.get("break_minutes", 0)
        color = request.POST.get("color", "#2563eb")
        if name and branch_id and start_time and end_time:
            from datetime import time
            st = time.fromisoformat(start_time)
            et = time.fromisoformat(end_time)
            ShiftTemplate.objects.create(
                name=name, branch_id=branch_id,
                start_time=st, end_time=et,
                break_minutes=break_minutes,
            )
            messages.success(request, f"Shift '{name}' created.")
            return redirect("shift_calendar")
        messages.error(request, "All fields are required.")
    from organisation.models import Branch
    return render(request, "staff/create_shift.html", {
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def monthly_payout(request):
    month_str = request.GET.get("month")
    branch_id = request.GET.get("branch")

    if month_str:
        try:
            target_date = datetime.strptime(month_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()

    month_start = target_date.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

    total_month_days = (month_end - month_start).days + 1

    try:
        bs_date = ad_to_bs(month_start)
        bs_display = f"{format_bs_date(*bs_date)}"
    except Exception:
        bs_display = month_str or str(month_start)

    staff_query = StaffProfile.objects.filter(status=StaffProfile.Status.ACTIVE).select_related("user", "branch")
    if branch_id:
        staff_query = staff_query.filter(branch_id=branch_id)

    approved_leaves = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=month_end,
        end_date__gte=month_start,
    ).select_related("leave_type", "staff")

    leave_map = {}
    for leave in approved_leaves:
        leave_start = max(leave.start_date, month_start)
        leave_end = min(leave.end_date, month_end)
        days = (leave_end - leave_start).days + 1
        key = leave.staff_id
        if key not in leave_map:
            leave_map[key] = {"paid_days": 0, "unpaid_days": 0, "leaves": []}
        if leave.leave_type.is_paid:
            leave_map[key]["paid_days"] += days
        else:
            leave_map[key]["unpaid_days"] += days
        leave_map[key]["leaves"].append(f"{leave.leave_type.name} ({days}d)")

    payout_data = []
    total_payout = Decimal("0")

    for staff in staff_query:
        entries = TimeEntry.objects.filter(
            staff=staff,
            clock_in__date__gte=month_start,
            clock_in__date__lte=month_end,
        )
        total_hours = sum((e.total_hours or 0) for e in entries)
        total_overtime = sum((e.overtime_hours or 0) for e in entries)
        working_days = entries.values("clock_in__date").distinct().count()

        leave_info = leave_map.get(staff.id, {"paid_days": 0, "unpaid_days": 0, "leaves": []})

        if staff.monthly_salary:
            per_day = staff.monthly_salary / Decimal(str(total_month_days))
            hourly_rate = staff.hourly_rate if staff.hourly_rate else (staff.monthly_salary / Decimal("208"))
            overtime_pay = Decimal(str(total_overtime)) * hourly_rate * Decimal("1.5")
            total_pay = staff.monthly_salary

            unpaid_leave_days = leave_info["unpaid_days"]
            if working_days < (total_month_days - unpaid_leave_days):
                absent_days = total_month_days - working_days - unpaid_leave_days
                if absent_days > 0:
                    total_pay = staff.monthly_salary - (per_day * Decimal(str(absent_days)))

            total_pay = total_pay + overtime_pay
            if total_pay < 0:
                total_pay = Decimal("0")
        else:
            hourly_rate = staff.hourly_rate if staff.hourly_rate else Decimal("0")
            total_pay = Decimal(str(total_hours)) * hourly_rate
            daily_pay = Decimal("0")
            overtime_pay = Decimal(str(total_overtime)) * hourly_rate
            total_pay = total_pay + overtime_pay

        total_payout += total_pay
        payout_data.append({
            "staff": staff,
            "working_days": working_days,
            "total_hours": total_hours,
            "total_overtime": total_overtime,
            "overtime_pay": round(overtime_pay, 2),
            "total_pay": round(total_pay, 2),
            "leave_days": leave_info["paid_days"] + leave_info["unpaid_days"],
            "unpaid_leave_days": leave_info["unpaid_days"],
            "leave_summary": ", ".join(leave_info["leaves"]) if leave_info["leaves"] else "-",
        })

    from organisation.models import Branch
    return render(request, "staff/monthly_payout.html", {
        "payout_data": payout_data,
        "target_month": month_start,
        "bs_display": bs_display,
        "total_payout": round(total_payout, 2),
        "branches": Branch.objects.filter(is_active=True),
        "total_month_days": total_month_days,
    })


@group_required("Admin", "Manager")
def attendance_report(request):
    date_str = request.GET.get("date")
    branch_id = request.GET.get("branch")
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    try:
        bs_date = ad_to_bs(target_date)
        bs_display = format_bs_date(*bs_date)
    except Exception:
        bs_display = str(target_date)

    staff_list = StaffProfile.objects.filter(status=StaffProfile.Status.ACTIVE).select_related("user", "branch")
    if branch_id:
        staff_list = staff_list.filter(branch_id=branch_id)

    entries = TimeEntry.objects.filter(clock_in__date=target_date).select_related("staff")

    attendance_data = []
    for staff in staff_list:
        entry = entries.filter(staff=staff).first()
        attendance_data.append({
            "staff": staff,
            "entry": entry,
            "present": entry is not None,
            "clock_in": entry.clock_in if entry else None,
            "clock_out": entry.clock_out if entry else None,
        })

    from organisation.models import Branch
    return render(request, "staff/attendance.html", {
        "attendance_data": attendance_data,
        "target_date": target_date,
        "bs_display": bs_display,
        "branches": Branch.objects.filter(is_active=True),
    })
