from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.permissions import group_required
from organisation.models import TableSession, Table
from .services import SessionService
from billing.workflows import SessionWorkflowService
from organisation.models import Branch, Floor
from .models import Expense, ExpenseCategory, CashRegister, CashMovement, DayEndSummary


def _ensure_default_categories():
    defaults = [
        "Food Supplies", "Beverages", "Utilities", "Rent",
        "Salary", "Maintenance", "Marketing", "Cleaning",
        "Equipment", "Transport", "Stationery", "Miscellaneous",
    ]
    for name in defaults:
        ExpenseCategory.objects.get_or_create(name=name, defaults={"is_active": True})


@group_required("Admin", "Manager", "Cashier", "Kitchen", "Waiter")
def session_list(request):
    sessions = TableSession.objects.filter(status=TableSession.Status.OPEN, is_deleted=False).select_related(
        "table", "table__floor", "table__floor__branch"
    ).order_by("-opened_at")
    return render(request, "sessions/session_list.html", {"sessions": sessions})


@group_required("Admin", "Manager", "Waiter")
def select_floor(request):
    floors = Floor.objects.filter(is_deleted=False, is_active=True).select_related("branch").prefetch_related(
        "tables"
    ).order_by("branch__name", "name")
    return render(request, "sessions/select_floor.html", {"floors": floors})


@group_required("Admin", "Manager", "Cashier", "Waiter")
@require_POST
def start_session(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    try:
        SessionService.start_session(table)
        messages.success(request, f"Session started for {table.name}.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("session_list")


@group_required("Admin", "Manager", "Cashier", "Kitchen", "Waiter")
def session_detail(request, session_id):
    session = get_object_or_404(
        TableSession.objects.select_related("table", "table__floor", "table__floor__branch").prefetch_related(
            "orders", "orders__items", "orders__items__menu_item"
        ),
        id=session_id,
    )
    try:
        bill = session.bill
    except Exception:
        bill = None
    return render(request, "operations/session_detail.html", {"session": session, "bill": bill})


@group_required("Admin", "Manager", "Cashier", "Waiter")
@require_POST
def close_session(request, session_id):
    session = get_object_or_404(TableSession, id=session_id)
    try:
        session, bill = SessionWorkflowService.close_session(session)
        messages.success(request, "Session closed.")
        return redirect("bill_detail", bill_id=bill.id)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("session_detail", session_id=session.id)


@group_required("Admin", "Manager")
def expense_list(request):
    _ensure_default_categories()
    expenses = Expense.objects.select_related("category", "branch", "recorded_by").all().order_by("-expense_date")
    category_id = request.GET.get("category")
    branch_id = request.GET.get("branch")
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if branch_id:
        expenses = expenses.filter(branch_id=branch_id)
    return render(request, "operations/expense_list.html", {
        "expenses": expenses,
        "categories": ExpenseCategory.objects.filter(is_active=True),
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def cash_register_list(request):
    registers = CashRegister.objects.select_related("branch", "opened_by").all().order_by("-opened_at")
    open_registers = [r for r in registers if r.status == CashRegister.Status.OPEN]
    return render(request, "operations/cash_register_list.html", {
        "registers": registers,
        "open_count": len(open_registers),
    })


@group_required("Admin", "Manager")
def open_cash_register(request):
    if request.method == "POST":
        branch_id = request.POST.get("branch")
        opening_balance = request.POST.get("opening_balance", 0)
        name = request.POST.get("name", "Main Register")
        if branch_id:
            reg = CashRegister.objects.create(
                branch_id=branch_id,
                name=name,
                opening_balance=opening_balance,
                opened_at=timezone.now(),
                opened_by=request.user,
            )
            messages.success(request, f"Cash register '{reg.name}' opened.")
            return redirect("cash_register_list")
        messages.error(request, "Branch is required.")
    from organisation.models import Branch
    return render(request, "operations/open_register.html", {
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def close_cash_register(request, register_id):
    reg = get_object_or_404(CashRegister, pk=register_id)
    if reg.status != CashRegister.Status.OPEN:
        messages.error(request, "Register is already closed.")
        return redirect("register_detail", register_id=reg.id)
    if request.method == "POST":
        closing_balance = request.POST.get("closing_balance", 0)
        reg.closing_balance = closing_balance
        reg.closed_at = timezone.now()
        reg.closed_by = request.user
        reg.status = CashRegister.Status.CLOSED
        reg.save(update_fields=["closing_balance", "closed_at", "closed_by", "status"])
        messages.success(request, f"Register '{reg.name}' closed.")
        return redirect("cash_register_list")
    total_sales = 0
    from billing.models import Payment
    from django.db.models import Sum
    payments = Payment.objects.filter(
        created_at__gte=reg.opened_at,
        created_at__lte=timezone.now(),
        payment_method="CASH"
    ).aggregate(total=Sum("amount_paid"))["total"] or 0
    movements_in = CashMovement.objects.filter(
        register=reg, movement_type__in=[CashMovement.MovementType.IN, CashMovement.MovementType.PAYMENT],
    ).aggregate(total=Sum("amount"))["total"] or 0
    movements_out = CashMovement.objects.filter(
        register=reg, movement_type= CashMovement.MovementType.OUT,
    ).aggregate(total=Sum("amount"))["total"] or 0
    expected_balance = reg.opening_balance + movements_in - movements_out
    return render(request, "operations/close_register.html", {
        "register": reg,
        "total_sales": payments,
        "movements_in": movements_in,
        "movements_out": movements_out,
        "expected_balance": expected_balance,
    })


@group_required("Admin", "Manager")
def register_detail(request, register_id):
    reg = get_object_or_404(
        CashRegister.objects.select_related("branch", "opened_by", "closed_by"),
        pk=register_id,
    )
    movements = CashMovement.objects.filter(register=reg).order_by("-created_at")[:50]
    return render(request, "operations/register_detail.html", {"register": reg, "movements": movements})


@group_required("Admin", "Manager")
def day_end_list(request):
    summaries = DayEndSummary.objects.select_related("branch", "closed_by").all().order_by("-summary_date")
    return render(request, "operations/day_end_list.html", {"summaries": summaries})


@group_required("Admin", "Manager")
def run_day_end(request):
    from django.utils import timezone
    from django.db.models import Sum
    from billing.models import Payment, Bill
    from datetime import date
    if request.method == "POST":
        branch_id = request.POST.get("branch")
        summary_date_str = request.POST.get("summary_date", str(date.today()))
        try:
            summary_date = date.fromisoformat(summary_date_str)
        except (ValueError, TypeError):
            summary_date = date.today()
        if branch_id:
            day_start = timezone.make_aware(
                timezone.datetime.combine(summary_date, timezone.datetime.min.time())
            )
            day_end = timezone.make_aware(
                timezone.datetime.combine(summary_date, timezone.datetime.max.time())
            )
            bills = Bill.objects.filter(
                branch_id=branch_id,
                generated_at__gte=day_start,
                generated_at__lte=day_end,
            )
            total_sales = bills.aggregate(s=Sum("grand_total"))["s"] or 0
            cash = Payment.objects.filter(
                bill__branch_id=branch_id, created_at__gte=day_start,
                created_at__lte=day_end, payment_method="CASH"
            ).aggregate(s=Sum("amount_paid"))["s"] or 0
            card = Payment.objects.filter(
                bill__branch_id=branch_id, created_at__gte=day_start,
                created_at__lte=day_end, payment_method="CARD"
            ).aggregate(s=Sum("amount_paid"))["s"] or 0
            online = Payment.objects.filter(
                bill__branch_id=branch_id, created_at__gte=day_start,
                created_at__lte=day_end
            ).exclude(payment_method__in=["CASH", "CARD"]).aggregate(
                s=Sum("amount_paid")
            )["s"] or 0
            expenses = Expense.objects.filter(
                branch_id=branch_id, expense_date=summary_date,
            ).aggregate(s=Sum("amount"))["s"] or 0
            order_count = bills.count()
            avg_bill = (total_sales / order_count) if order_count > 0 else 0
            net_revenue = total_sales - expenses

            summary, created = DayEndSummary.objects.update_or_create(
                branch_id=branch_id, summary_date=summary_date,
                defaults={
                    "total_sales": total_sales,
                    "total_expenses": expenses,
                    "total_cash": cash,
                    "total_card": card,
                    "total_online": online,
                    "total_orders": order_count,
                    "net_revenue": net_revenue,
                    "average_bill": avg_bill,
                    "is_closed": True,
                    "closed_at": timezone.now(),
                    "closed_by": request.user,
                }
            )
            messages.success(request, f"Day end summary created for {summary_date}.")
            return redirect("day_end_list")
        messages.error(request, "Branch is required.")
    from organisation.models import Branch
    return render(request, "operations/run_day_end.html", {
        "branches": Branch.objects.filter(is_active=True),
        "today": date.today().isoformat(),
    })


@group_required("Admin", "Manager")
def create_expense(request):
    _ensure_default_categories()
    from django.utils import timezone
    if request.method == "POST":
        category_id = request.POST.get("category")
        branch_id = request.POST.get("branch")
        amount = request.POST.get("amount")
        description = request.POST.get("description", "")
        expense_date = request.POST.get("expense_date", timezone.now().date())
        if category_id and branch_id and amount:
            expense = Expense.objects.create(category_id=category_id, branch_id=branch_id, amount=amount, description=description, expense_date=expense_date, recorded_by=request.user)
            messages.success(request, f"Expense of Rs.{amount} recorded.")
            return redirect("expense_list")
        messages.error(request, "Category, branch, and amount are required.")
    return render(request, "operations/create_expense.html", {
        "categories": ExpenseCategory.objects.filter(is_active=True),
        "branches": Branch.objects.filter(is_active=True),
    })
