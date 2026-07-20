from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import models
from core.permissions import group_required
from .models import Bill, Payment
from .services import BillingService


@group_required("Admin", "Manager", "Cashier")
def pay_bill(request, bill_id):
    bill = get_object_or_404(
        Bill.objects.select_related("session__table__floor__branch", "branch"), id=bill_id)

    if request.method == "POST":
        method = request.POST.get("method", "CASH")
        reference = request.POST.get("reference_number", "")
        amount = request.POST.get("amount", "")

        try:
            amount_paid = Decimal(amount) if amount else bill.grand_total
        except Exception:
            amount_paid = bill.grand_total

        try:
            BillingService.record_payment(
                bill=bill, amount_paid=amount_paid,
                payment_method=method, reference_number=reference,
            )
            messages.success(request, "Payment recorded successfully.")
            return redirect("bill_detail", bill_id=bill.id)
        except ValueError as e:
            return render(request, "billing/pay_bill.html", {"bill": bill, "error": str(e)})

    remaining = bill.grand_total - (bill.payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0)
    return render(request, "billing/pay_bill.html", {"bill": bill, "remaining": remaining})


@group_required("Admin", "Manager", "Cashier")
def bill_detail(request, bill_id):
    bill = get_object_or_404(
        Bill.objects.select_related("session", "session__table").prefetch_related("payments"),
        id=bill_id,
    )
    payments = bill.payments.all()
    paid_total = payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0
    remaining = max(bill.grand_total - paid_total, Decimal("0"))

    from coupons.models import Coupon
    valid_coupons = []
    if not bill.coupon_code and paid_total == 0:
        for c in Coupon.objects.filter(is_active=True).order_by("code"):
            if c.is_valid and bill.subtotal >= c.minimum_order_amount:
                valid_coupons.append(c)

    return render(request, "billing/bill_detail.html", {
        "bill": bill, "payments": payments, "paid_total": paid_total,
        "remaining": remaining, "valid_coupons": valid_coupons,
    })


@group_required("Admin", "Manager", "Cashier")
def bill_list(request):
    from decimal import Decimal
    from django.db.models import Sum, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    paid_sub = Payment.objects.filter(bill=OuterRef("pk")).values("bill").annotate(
        total=Sum("amount_paid")
    ).values("total")[:1]
    bills = Bill.objects.select_related(
        "session", "session__table", "session__table__floor", "session__table__floor__branch"
    ).annotate(
        paid_amount=Coalesce(Subquery(paid_sub), Value(Decimal("0")))
    ).order_by("-generated_at")
    return render(request, "billing/bill_list.html", {"bills": bills})


@group_required("Admin", "Manager", "Cashier")
def online_payment(request, bill_id, gateway):
    bill = get_object_or_404(Bill, id=bill_id)
    try:
        url = BillingService.get_online_payment_url(bill, gateway, request=request)
        return redirect(url)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("pay_bill", bill_id=bill_id)


@group_required("Admin", "Manager", "Cashier")
def payment_success(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    ref_id = request.GET.get("refId", "")
    amt = request.GET.get("amt", "")
    try:
        from decimal import Decimal
        amount = Decimal(amt) if amt else bill.grand_total
        BillingService.record_payment(
            bill=bill, amount_paid=amount,
            payment_method="ESEWA", reference_number=ref_id,
        )
        messages.success(request, f"eSewa payment successful. Ref: {ref_id}")
    except ValueError as e:
        messages.warning(request, f"Payment recorded manually: {e}")
    return redirect("bill_detail", bill_id=bill_id)


@group_required("Admin", "Manager", "Cashier")
def payment_failed(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    messages.error(request, "Online payment failed or was cancelled. Please try again.")
    return redirect("pay_bill", bill_id=bill_id)


@group_required("Admin", "Manager", "Cashier")
def print_bill(request, bill_id):
    bill = get_object_or_404(
        Bill.objects.select_related("session", "session__table", "session__table__floor", "session__table__floor__branch", "branch").prefetch_related(
            "payments", "session__orders", "session__orders__items", "session__orders__items__menu_item", "quick_items"
        ),
        id=bill_id,
    )
    payments = bill.payments.all()
    paid_total = payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0
    balance = max(bill.grand_total - paid_total, 0)
    return render(request, "billing/print_bill.html", {
        "bill": bill, "payments": payments, "balance": balance,
    })


@group_required("Admin", "Manager", "Cashier")
def apply_coupon(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code", "").strip()
        if coupon_code:
            try:
                BillingService.apply_coupon(bill, coupon_code)
                messages.success(request, f"Coupon '{coupon_code.upper()}' applied! Discount: Rs.{bill.discount_amount}.")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please enter a coupon code.")
    return redirect("bill_detail", bill_id=bill_id)
