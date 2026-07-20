from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.permissions import group_required
from .models import PayrollPeriod, Payslip, LeaveRequest, LeaveType, LeaveBalance
from .services import PayrollService


@group_required("Admin", "Manager")
def payroll_periods(request):
    periods = PayrollPeriod.objects.select_related("branch").all().order_by("-start_date")
    return render(request, "payroll/periods.html", {"periods": periods})


@group_required("Admin", "Manager")
def payslip_list(request, period_id):
    period = get_object_or_404(PayrollPeriod, pk=period_id)
    payslips = Payslip.objects.select_related("staff", "staff__user").filter(period=period)
    return render(request, "payroll/payslips.html", {"period": period, "payslips": payslips})


@group_required("Admin", "Manager")
def payslip_detail(request, payslip_id):
    payslip = get_object_or_404(
        Payslip.objects.select_related("staff", "staff__user", "period", "period__branch"),
        pk=payslip_id,
    )
    return render(request, "payroll/payslip_detail.html", {"payslip": payslip})


@group_required("Admin", "Manager")
def process_payroll(request, period_id):
    if request.method == "POST":
        try:
            PayrollService.process_period(period_id)
            messages.success(request, "Payroll processed successfully.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("payslip_list", period_id=period_id)


@group_required("Admin", "Manager")
def leave_requests(request):
    leaves = LeaveRequest.objects.select_related("staff", "staff__user", "leave_type", "approved_by").all().order_by("-created_at")
    status_filter = request.GET.get("status")
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    return render(request, "payroll/leave_requests.html", {"leaves": leaves})


@group_required("Admin", "Manager")
@require_POST
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id)
    leave.status = LeaveRequest.Status.APPROVED
    leave.approved_by = request.user
    leave.approved_at = timezone.now()
    leave.save(update_fields=["status", "approved_by", "approved_at"])

    try:
        year = leave.start_date.year
        balance, _ = LeaveBalance.objects.get_or_create(
            staff=leave.staff,
            leave_type=leave.leave_type,
            year=year,
            defaults={"total_days": leave.leave_type.days_per_year, "used_days": 0, "pending_days": 0},
        )
        leave_days = leave.days_count
        balance.used_days += leave_days
        balance.pending_days = max(0, balance.pending_days - leave_days)
        balance.save(update_fields=["used_days", "pending_days"])
    except Exception:
        pass

    messages.success(request, f"Leave approved ({leave.days_count} days).")
    return redirect("leave_requests")


@group_required("Admin", "Manager")
@require_POST
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id)
    leave.status = LeaveRequest.Status.REJECTED
    leave.approved_by = request.user
    leave.approved_at = timezone.now()
    leave.save(update_fields=["status", "approved_by", "approved_at"])
    messages.success(request, "Leave rejected.")
    return redirect("leave_requests")


@group_required("Admin", "Manager")
def create_leave_request(request):
    from staff.models import StaffProfile
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        leave_type_id = request.POST.get("leave_type")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason", "")
        if staff_id and leave_type_id and start_date and end_date:
            from datetime import datetime
            leave = LeaveRequest.objects.create(
                staff_id=staff_id, leave_type_id=leave_type_id,
                start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
                reason=reason,
            )
            messages.success(request, "Leave request submitted.")
            return redirect("leave_requests")
        messages.error(request, "All fields are required.")
    return render(request, "payroll/create_leave.html", {
        "staff_list": StaffProfile.objects.filter(status="ACTIVE").select_related("user"),
        "leave_types": LeaveType.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def leave_type_list(request):
    leave_types = LeaveType.objects.all().order_by("name")
    return render(request, "payroll/leave_types.html", {"leave_types": leave_types})


@group_required("Admin", "Manager")
def create_leave_type(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        days_per_year = request.POST.get("days_per_year", 0)
        is_paid = request.POST.get("is_paid") == "on"
        requires_approval = request.POST.get("requires_approval") == "on"
        if name:
            LeaveType.objects.create(
                name=name, description=description,
                days_per_year=int(days_per_year or 0),
                is_paid=is_paid,
                requires_approval=requires_approval,
            )
            messages.success(request, f"Leave type '{name}' created.")
            return redirect("leave_type_list")
        messages.error(request, "Name is required.")
    return render(request, "payroll/create_leave_type.html")


@group_required("Admin", "Manager")
def create_payroll_period(request):
    if request.method == "POST":
        name = request.POST.get("name")
        branch_id = request.POST.get("branch")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        if name and branch_id and start_date and end_date:
            from datetime import datetime
            period = PayrollPeriod.objects.create(
                name=name, branch_id=branch_id, start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
            )
            messages.success(request, f"Payroll period '{period.name}' created.")
            return redirect("payroll_periods")
        messages.error(request, "All fields are required.")
    from organisation.models import Branch
    return render(request, "payroll/create_period.html", {"branches": Branch.objects.filter(is_active=True)})
