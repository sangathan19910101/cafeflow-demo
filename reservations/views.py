from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.permissions import group_required
from crm.models import Customer
from organisation.models import Table
from .models import Reservation, WaitlistEntry
from .services import ReservationService


@group_required("Admin", "Manager", "Waiter")
def reservation_list(request):
    status = request.GET.get("status")
    date = request.GET.get("date")
    search = request.GET.get("search")
    reservations = Reservation.objects.select_related("customer", "branch").prefetch_related("tables").all()
    if status:
        reservations = reservations.filter(status=status)
    if date:
        reservations = reservations.filter(reservation_date=date)
    if search:
        reservations = reservations.filter(
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    reservations = reservations.order_by("reservation_date", "reservation_time")
    waitlist = WaitlistEntry.objects.filter(status=WaitlistEntry.Status.WAITING).select_related("customer", "branch")
    return render(request, "reservations/list.html", {
        "reservations": reservations,
        "waitlist": waitlist,
    })


@group_required("Admin", "Manager")
def confirm_reservation(request, reservation_id):
    try:
        ReservationService.confirm_reservation(reservation_id)
        messages.success(request, "Reservation confirmed and table assigned.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("reservation_list")


@group_required("Admin", "Manager", "Waiter")
def cancel_reservation(request, reservation_id):
    if request.method == "POST":
        reason = request.POST.get("reason", "")
        try:
            ReservationService.cancel_reservation(reservation_id, reason)
            messages.success(request, "Reservation cancelled. Table released.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("reservation_list")


@group_required("Admin", "Manager", "Waiter")
def mark_seated(request, reservation_id):
    try:
        ReservationService.mark_seated(reservation_id)
        messages.success(request, "Guest seated. Table session opened.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("reservation_list")


@group_required("Admin", "Manager", "Waiter")
def notify_waitlist(request, entry_id):
    entry = get_object_or_404(WaitlistEntry, pk=entry_id)
    entry.status = WaitlistEntry.Status.NOTIFIED
    entry.notified_at = timezone.now()
    entry.save(update_fields=["status", "notified_at"])
    messages.success(request, f"Notified {entry.customer.name}.")
    return redirect("reservation_list")


@group_required("Admin", "Manager", "Waiter")
def create_reservation(request):
    from organisation.models import Branch
    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        customer_name = request.POST.get("customer_name", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        branch_id = request.POST.get("branch")
        guest_count = request.POST.get("guest_count")
        res_date = request.POST.get("reservation_date")
        res_time = request.POST.get("reservation_time")
        special_requests = request.POST.get("special_requests", "")
        table_ids = request.POST.getlist("tables")

        if branch_id and guest_count and res_date and res_time:
            from datetime import datetime

            if customer_id:
                customer = get_object_or_404(Customer, pk=customer_id)
            elif customer_name and customer_phone:
                customer, _ = Customer.objects.get_or_create(
                    phone=customer_phone,
                    defaults={"name": customer_name},
                )
            else:
                messages.error(request, "Customer is required.")
                return render(request, "reservations/create_reservation.html", {
                    "branches": Branch.objects.filter(is_active=True),
                    "customers": Customer.objects.all().order_by("name"),
                })

            branch = Branch.objects.get(pk=branch_id)
            reservation_data = {
                "branch": branch,
                "guest_count": int(guest_count),
                "reservation_date": datetime.strptime(res_date, "%Y-%m-%d").date(),
                "reservation_time": datetime.strptime(res_time, "%H:%M").time(),
                "special_requests": special_requests,
                "table_ids": table_ids if table_ids else None,
            }
            try:
                ReservationService.create_reservation(
                    {"name": customer.name, "phone": customer.phone, "email": customer.email},
                    reservation_data,
                )
                messages.success(request, "Reservation created." + (" Table assigned." if table_ids else ""))
            except Exception as e:
                messages.error(request, str(e))
            return redirect("reservation_list")
        messages.error(request, "Branch, guest count, date, and time are required.")

    return render(request, "reservations/create_reservation.html", {
        "branches": Branch.objects.filter(is_active=True),
        "customers": Customer.objects.all().order_by("name"),
    })


@group_required("Admin", "Manager", "Waiter")
def customer_lookup(request):
    query = request.GET.get("q", "")
    if query:
        customers = Customer.objects.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )[:20]
    else:
        customers = Customer.objects.all()[:20]
    data = [
        {
            "id": str(c.id),
            "name": c.name,
            "phone": c.phone,
            "email": c.email or "",
            "visit_count": c.visit_count,
            "is_vip": c.is_vip,
        }
        for c in customers
    ]
    return JsonResponse({"customers": data})


@group_required("Admin", "Manager", "Waiter")
def available_tables(request):
    branch_id = request.GET.get("branch")
    guest_count = request.GET.get("guests", 1)
    if branch_id:
        tables = Table.objects.filter(
            floor__branch_id=branch_id,
            status=Table.Status.AVAILABLE,
            capacity__gte=int(guest_count),
            is_active=True,
        ).select_related("floor").order_by("capacity", "name")
    else:
        tables = Table.objects.filter(
            status=Table.Status.AVAILABLE,
            is_active=True,
        ).select_related("floor").order_by("capacity", "name")
    data = [
        {
            "id": str(t.id),
            "name": t.name,
            "capacity": t.capacity,
            "floor": t.floor.name,
        }
        for t in tables
    ]
    return JsonResponse({"tables": data})
