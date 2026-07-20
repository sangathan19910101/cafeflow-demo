from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.permissions import group_required
from .models import KDSDisplay
from .services import KDSService


@group_required("Admin", "Manager", "Kitchen")
def kds_dashboard(request):
    branch_id = request.GET.get("branch")
    entries = KDSDisplay.objects.select_related(
        "order", "order__session", "order__session__table", "branch"
    ).order_by("priority", "created_at")
    if branch_id:
        entries = entries.filter(branch_id=branch_id)
    pending = entries.filter(status=KDSDisplay.Status.PENDING)
    preparing = entries.filter(status=KDSDisplay.Status.PREPARING)
    ready = entries.filter(status=KDSDisplay.Status.READY)
    served = entries.filter(status=KDSDisplay.Status.SERVED)
    return render(request, "kds/dashboard.html", {
        "pending": pending,
        "preparing": preparing,
        "ready": ready,
        "served": served,
    })


@group_required("Admin", "Manager", "Kitchen")
@require_POST
def start_preparing(request, entry_id):
    try:
        KDSService.start_preparing(entry_id)
        messages.success(request, "Order is now being prepared.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("kds_dashboard")


@group_required("Admin", "Manager", "Kitchen")
@require_POST
def mark_ready(request, entry_id):
    try:
        KDSService.mark_ready(entry_id)
        messages.success(request, "Order is ready for serving.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("kds_dashboard")


@group_required("Admin", "Manager", "Waiter")
@require_POST
def mark_served(request, entry_id):
    try:
        KDSService.mark_served(entry_id)
        messages.success(request, "Order has been served.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("kds_dashboard")
