
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.permissions import group_required
from .services import OrderService
from .models import Order
from .forms import OrderItemForm

from organisation.models import TableSession


@group_required("Admin", "Manager", "Waiter")
@require_POST
def create_order(request, session_id):

    session = get_object_or_404(
        TableSession,
        id=session_id,
    )

    try:
        order = OrderService.create_order(
            session
        )

    except ValueError as e:

        messages.error(
            request,
            str(e),
        )

        return redirect(
            "session_detail",
            session_id=session.id,
        )

    return redirect(
        "order_detail",
        order_id=order.id,
    )


@group_required(
    "Admin",
    "Manager",
    "Cashier",
    "Kitchen",
    "Waiter",
)
def order_detail(
    request,
    order_id,
):

    order = get_object_or_404(
        Order.objects.select_related(
            "session",
            "session__table",
            "session__table__floor",
            "session__table__floor__branch",
        ).prefetch_related(
            "items",
        ),
        id=order_id,
    )

    total = sum(
        item.quantity * item.price_snapshot
        for item in order.items.all()
    )

    context = {
        "order": order,
        "total": total,
    }

    return render(
        request,
        "orders/order_detail.html",
        context,
    )


@group_required(
    "Admin",
    "Manager",
    "Waiter",
)
def add_order_item(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if request.method == "POST":

        form = OrderItemForm(
            request.POST
        )

        if form.is_valid():

            try:

                OrderService.add_item(
                    order=order,
                    menu_item=form.cleaned_data["menu_item"],
                    quantity=form.cleaned_data["quantity"],
                    notes=form.cleaned_data["notes"],
                )

                return redirect(
                    "order_detail",
                    order_id=order.id,
                )

            except ValueError as e:

                form.add_error(
                    None,
                    str(e),
                )

    else:

        form = OrderItemForm()

    context = {
        "order": order,
        "form": form,
    }

    return render(
        request,
        "orders/add_order_item.html",
        context,
    )


@group_required("Admin", "Manager", "Waiter")
@require_POST
def submit_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    try:

        OrderService.submit_order(
            order
        )

    except ValueError as e:

        messages.error(
            request,
            str(e),
        )

    return redirect(
        "order_detail",
        order_id=order.id,
    )


@group_required("Admin", "Manager", "Kitchen")
@require_POST
def accept_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    try:

        OrderService.accept_order(
            order
        )

    except ValueError as e:

        messages.error(
            request,
            str(e),
        )

    return redirect(
        "order_detail",
        order_id=order.id,
    )


@group_required("Admin", "Manager", "Kitchen")
@require_POST
def reject_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    try:

        OrderService.reject_order(
            order
        )

    except ValueError as e:

        messages.error(
            request,
            str(e),
        )

    return redirect(
        "order_detail",
        order_id=order.id,
    )


@group_required("Admin", "Manager", "Waiter")
@require_POST
def cancel_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    try:

        OrderService.cancel_order(
            order
        )

    except ValueError as e:

        messages.error(
            request,
            str(e),
        )

    return redirect(
        "order_detail",
        order_id=order.id,
    )


@group_required(
    "Admin",
    "Manager",
    "Cashier",
    "Kitchen",
    "Waiter",
)
def order_list(request):

    status = request.GET.get(
        "status"
    )

    orders = Order.objects.select_related(
        "session",
        "session__table",
    )

    if status:

        orders = orders.filter(
            status=status
        )

    orders = orders.order_by(
        "-created_at"
    )

    context = {
        "orders": orders,
        "current_status": status,
    }

    return render(
        request,
        "orders/order_list.html",
        context,
    )
