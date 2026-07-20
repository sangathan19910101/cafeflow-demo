from django.db import transaction
from django.utils import timezone
from organisation.models import TableSession
from menu.models import MenuItem
from .models import Order, OrderItem


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(session: TableSession):
        session = TableSession.objects.select_for_update().get(pk=session.pk)
        if session.status != TableSession.Status.OPEN:
            raise ValueError("Cannot create order in closed session.")
        order = Order.objects.create(session=session, status=Order.Status.DRAFT)
        return order

    @staticmethod
    @transaction.atomic
    def submit_order(order: Order):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.session.status != TableSession.Status.OPEN:
            raise ValueError("Cannot submit order from closed session.")
        if order.status != Order.Status.DRAFT:
            raise ValueError("Only draft orders can be submitted.")
        if not order.items.exists():
            raise ValueError("Cannot submit an empty order.")
        order.status = Order.Status.SUBMITTED
        order.submitted_at = timezone.now()
        order.save(update_fields=["status", "submitted_at"])
        return order

    @staticmethod
    @transaction.atomic
    def accept_order(order: Order):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != Order.Status.SUBMITTED:
            raise ValueError("Only submitted orders can be accepted.")
        order.status = Order.Status.ACCEPTED
        order.accepted_at = timezone.now()
        order.save(update_fields=["status", "accepted_at"])

        try:
            from inventory.services import InventoryService
            for item in order.items.select_related("menu_item").all():
                InventoryService.consume_ingredients(item.menu_item, item.quantity)
        except Exception:
            pass

        try:
            from kds.services import KDSService
            KDSService.create_kds_entry(order)
        except Exception:
            pass

        return order

    @staticmethod
    @transaction.atomic
    def reject_order(order: Order):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != Order.Status.SUBMITTED:
            raise ValueError("Only submitted orders can be rejected.")
        order.status = Order.Status.REJECTED
        order.rejected_at = timezone.now()
        order.save(update_fields=["status", "rejected_at"])
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != Order.Status.DRAFT:
            raise ValueError("Only draft orders can be cancelled.")
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        return order

    @staticmethod
    @transaction.atomic
    def add_item(order, menu_item: MenuItem, quantity: int, notes=""):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != Order.Status.DRAFT:
            raise ValueError("Items can only be added to draft orders.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if not menu_item.is_available:
            raise ValueError("Menu item is unavailable.")
        if not menu_item.category.is_active:
            raise ValueError("Menu category is inactive.")
        if order.items.filter(menu_item=menu_item).exists():
            raise ValueError("Menu item already exists in this order.")
        item = OrderItem.objects.create(
            order=order, menu_item=menu_item,
            quantity=quantity, price_snapshot=menu_item.price,
            notes=notes,
        )
        return item
