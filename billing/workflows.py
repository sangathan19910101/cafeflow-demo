from django.db import transaction
from django.utils import timezone
from organisation.models import TableSession, Table
from orders.models import Order
from billing.services import BillingService


class SessionWorkflowService:
    @staticmethod
    @transaction.atomic
    def close_session(session: TableSession):
        session = TableSession.objects.select_for_update().select_related("table").get(pk=session.pk)
        if session.status != TableSession.Status.OPEN:
            raise ValueError("Only open sessions can be closed.")
        unsafe_orders = session.orders.exclude(status__in=[
            Order.Status.ACCEPTED, Order.Status.REJECTED, Order.Status.CANCELLED,
            Order.Status.SUBMITTED,
        ])
        if unsafe_orders.exists():
            raise ValueError("Cannot close session while draft orders exist. Please submit or cancel them.")
        bill = getattr(session, "bill", None)
        if not bill:
            bill = BillingService.generate_bill(session=session)
        session.status = TableSession.Status.CLOSED
        session.closed_at = timezone.now()
        session.total_amount = bill.grand_total
        session.is_billed = True
        session.save(update_fields=["status", "closed_at", "total_amount", "is_billed"])
        table = session.table
        table.status = Table.Status.CLEANING
        table.save(update_fields=["status"])
        return session, bill
