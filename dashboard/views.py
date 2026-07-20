from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from core.permissions import group_required
from organisation.models import Branch, Floor, Table, TableSession
from orders.models import Order, OrderItem
from billing.models import Bill, Payment


@group_required("Admin", "Manager", "Cashier", "Kitchen", "Waiter")
def dashboard(request):
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    total_revenue = Bill.objects.aggregate(total=Sum("grand_total"))["total"] or 0
    today_revenue = Bill.objects.filter(generated_at__gte=today_start).aggregate(total=Sum("grand_total"))["total"] or 0
    avg_bill = Bill.objects.aggregate(avg=Avg("grand_total"))["avg"] or 0

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.Status.SUBMITTED).count()
    accepted_orders = Order.objects.filter(status=Order.Status.ACCEPTED).count()

    active_sessions = TableSession.objects.select_related(
        "table", "table__floor", "table__floor__branch"
    ).filter(status=TableSession.Status.OPEN, is_deleted=False).order_by("-opened_at")[:5]

    open_session_count = TableSession.objects.filter(status=TableSession.Status.OPEN, is_deleted=False).count()
    available_table_count = Table.objects.filter(status=Table.Status.AVAILABLE, is_deleted=False).count()
    occupied_table_count = Table.objects.filter(status=Table.Status.OCCUPIED, is_deleted=False).count()
    reserved_table_count = Table.objects.filter(status=Table.Status.RESERVED, is_deleted=False).count()

    recent_orders = Order.objects.select_related("session__table").order_by("-created_at")[:5]
    recent_payments = Payment.objects.select_related("bill__session__table").order_by("-paid_at")[:5]

    low_stock_count = 0
    try:
        from inventory.models import InventoryItem
        low_stock_count = InventoryItem.objects.filter(is_active=True, quantity_in_stock__lte=F("low_stock_threshold")).count()
    except Exception:
        pass

    today_orders_count = Order.objects.filter(created_at__gte=today_start).count()
    today_sessions_count = TableSession.objects.filter(opened_at__gte=today_start).count()

    branch_stats = Branch.objects.filter(is_deleted=False).annotate(
        table_count=Count("floors__tables"),
        active_sessions=Count("floors__tables__sessions", filter=Q(floors__tables__sessions__status=TableSession.Status.OPEN)),
    )

    context = {
        "branch_count": Branch.objects.filter(is_deleted=False).count(),
        "floor_count": Floor.objects.filter(is_deleted=False).count(),
        "table_count": Table.objects.filter(is_deleted=False).count(),
        "open_session_count": open_session_count,
        "available_table_count": available_table_count,
        "occupied_table_count": occupied_table_count,
        "reserved_table_count": reserved_table_count,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "accepted_orders": accepted_orders,
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "avg_bill": avg_bill,
        "today_orders_count": today_orders_count,
        "today_sessions_count": today_sessions_count,
        "low_stock_count": low_stock_count,
        "recent_orders": recent_orders,
        "active_sessions": active_sessions,
        "recent_payments": recent_payments,
        "branch_stats": branch_stats,
    }
    return render(request, "dashboard/dashboard.html", context)



