from django.db import transaction
from django.utils import timezone
from orders.models import Order
from .models import KDSDisplay


class KDSService:
    @staticmethod
    @transaction.atomic
    def create_kds_entry(order: Order):
        entry, created = KDSDisplay.objects.get_or_create(
            order=order,
            defaults={
                "branch": order.session.table.floor.branch,
                "status": KDSDisplay.Status.PENDING,
            },
        )
        return entry

    @staticmethod
    @transaction.atomic
    def start_preparing(entry_id):
        entry = KDSDisplay.objects.select_for_update().get(pk=entry_id)
        if entry.status != KDSDisplay.Status.PENDING:
            raise ValueError("Only pending orders can be moved to preparing.")
        entry.status = KDSDisplay.Status.PREPARING
        entry.started_at = timezone.now()
        entry.save(update_fields=["status", "started_at"])
        return entry

    @staticmethod
    @transaction.atomic
    def mark_ready(entry_id):
        entry = KDSDisplay.objects.select_for_update().get(pk=entry_id)
        if entry.status != KDSDisplay.Status.PREPARING:
            raise ValueError("Only preparing orders can be marked ready.")
        entry.status = KDSDisplay.Status.READY
        entry.completed_at = timezone.now()
        entry.save(update_fields=["status", "completed_at"])
        return entry

    @staticmethod
    @transaction.atomic
    def mark_served(entry_id):
        entry = KDSDisplay.objects.select_for_update().get(pk=entry_id)
        if entry.status != KDSDisplay.Status.READY:
            raise ValueError("Only ready orders can be marked served.")
        entry.status = KDSDisplay.Status.SERVED
        entry.save(update_fields=["status"])
        return entry
