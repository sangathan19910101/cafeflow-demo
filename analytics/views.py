from django.shortcuts import render
from django.db.models import Sum, Avg, Max, Min, Count, F, DecimalField
from core.permissions import group_required
from orders.models import Order, OrderItem
from billing.models import Bill, Payment
from organisation.models import TableSession, Table, Branch
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta


@group_required("Admin", "Manager")
def analytics_dashboard(request):
    branch_id = request.GET.get("branch")
    period = request.GET.get("period", "30")
    days = int(period) if period.isdigit() else 30
    cutoff = timezone.now() - timedelta(days=days)

    bill_qs = Bill.objects.all()
    order_qs = Order.objects.all()
    session_qs = TableSession.objects.all()
    order_item_qs = OrderItem.objects.filter(order__status=Order.Status.ACCEPTED)

    if branch_id:
        bill_qs = bill_qs.filter(session__table__floor__branch_id=branch_id)
        order_qs = order_qs.filter(session__table__floor__branch_id=branch_id)
        session_qs = session_qs.filter(table__floor__branch_id=branch_id)
        order_item_qs = order_item_qs.filter(order__session__table__floor__branch_id=branch_id)

    revenue_stats = bill_qs.aggregate(
        total_revenue=Sum("grand_total"),
        average_bill=Avg("grand_total"),
        highest_bill=Max("grand_total"),
        lowest_bill=Min("grand_total"),
    )

    total_revenue = revenue_stats["total_revenue"] or 0
    average_bill = revenue_stats["average_bill"] or 0
    highest_bill = revenue_stats["highest_bill"] or 0
    lowest_bill = revenue_stats["lowest_bill"] or 0

    total_orders = order_qs.count()
    accepted_orders = order_qs.filter(status=Order.Status.ACCEPTED).count()
    rejected_orders = order_qs.filter(status=Order.Status.REJECTED).count()
    cancelled_orders = order_qs.filter(status=Order.Status.CANCELLED).count()
    draft_orders = order_qs.filter(status=Order.Status.DRAFT).count()
    submitted_orders = order_qs.filter(status=Order.Status.SUBMITTED).count()

    total_sessions = session_qs.count()
    open_sessions_count = session_qs.filter(status=TableSession.Status.OPEN).count()
    closed_sessions_count = session_qs.filter(status=TableSession.Status.CLOSED).count()

    acceptance_rate = round((accepted_orders / total_orders * 100), 2) if total_orders > 0 else 0
    rejection_rate = round((rejected_orders / total_orders * 100), 2) if total_orders > 0 else 0
    cancellation_rate = round((cancelled_orders / total_orders * 100), 2) if total_orders > 0 else 0

    top_selling_items = (
        order_item_qs.values("menu_item__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:10]
    )

    revenue_per_item = (
        order_item_qs.values("menu_item__name")
        .annotate(total_revenue=Sum(F("quantity") * F("price_snapshot"), output_field=DecimalField(max_digits=12, decimal_places=2)))
        .order_by("-total_revenue")[:10]
    )

    category_performance = (
        order_item_qs.values("menu_item__category__name")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum(F("quantity") * F("price_snapshot"), output_field=DecimalField(max_digits=12, decimal_places=2)))
        .order_by("-total_revenue")
    )

    revenue_trend = (
        bill_qs.filter(generated_at__gte=cutoff)
        .annotate(revenue_date=TruncDate("generated_at"))
        .values("revenue_date")
        .annotate(daily_revenue=Sum("grand_total"))
        .order_by("revenue_date")
    )

    payment_methods = (
        Payment.objects.values("payment_method")
        .annotate(total=Sum("amount_paid"), count=Count("id"))
        .order_by("-total")
    )

    branch_revenue = (
        Bill.objects.values("session__table__floor__branch__name")
        .annotate(total=Sum("grand_total"), count=Count("id"), avg=Avg("grand_total"))
        .order_by("-total")
    )

    most_used_tables = (
        Table.objects.select_related("floor").annotate(session_count=Count("sessions")).order_by("-session_count")[:10]
    )

    recent_bills = bill_qs.select_related("session__table").order_by("-generated_at")[:10]

    context = {
        "total_revenue": total_revenue, "average_bill": average_bill,
        "highest_bill": highest_bill, "lowest_bill": lowest_bill,
        "total_orders": total_orders, "draft_orders": draft_orders,
        "submitted_orders": submitted_orders, "accepted_orders": accepted_orders,
        "rejected_orders": rejected_orders, "cancelled_orders": cancelled_orders,
        "acceptance_rate": acceptance_rate, "rejection_rate": rejection_rate,
        "cancellation_rate": cancellation_rate,
        "total_sessions": total_sessions, "open_sessions_count": open_sessions_count,
        "closed_sessions_count": closed_sessions_count,
        "top_selling_items": top_selling_items, "revenue_per_item": revenue_per_item,
        "category_performance": category_performance, "revenue_trend": revenue_trend,
        "recent_bills": recent_bills, "most_used_tables": most_used_tables,
        "payment_methods": payment_methods, "branch_revenue": branch_revenue,
        "branches": Branch.objects.filter(is_deleted=False, is_active=True),
        "selected_branch": branch_id, "selected_period": period,
    }
    return render(request, "analytics/dashboard.html", context)
