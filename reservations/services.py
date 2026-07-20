from django.db import transaction
from django.utils import timezone
from organisation.models import Table, TableSession
from crm.models import Customer
from .models import Reservation


class ReservationService:
    @staticmethod
    @transaction.atomic
    def create_reservation(customer_data, reservation_data):
        customer, _ = Customer.objects.get_or_create(
            phone=customer_data.get("phone", ""),
            defaults={"name": customer_data.get("name", ""), "email": customer_data.get("email", "")},
        )
        if customer_data.get("name") and customer.name != customer_data["name"]:
            customer.name = customer_data["name"]
            customer.save(update_fields=["name"])

        reservation = Reservation.objects.create(
            customer=customer,
            branch=reservation_data["branch"],
            guest_count=reservation_data["guest_count"],
            reservation_date=reservation_data["reservation_date"],
            reservation_time=reservation_data["reservation_time"],
            duration_minutes=reservation_data.get("duration_minutes", 120),
            special_requests=reservation_data.get("special_requests", ""),
        )

        if reservation_data.get("table_ids"):
            tables = Table.objects.filter(id__in=reservation_data["table_ids"])
            reservation.tables.set(tables)
            tables.update(status=Table.Status.RESERVED)

        return reservation

    @staticmethod
    @transaction.atomic
    def confirm_reservation(reservation_id):
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        if reservation.status != Reservation.Status.PENDING:
            raise ValueError("Only pending reservations can be confirmed.")

        tables = reservation.tables.filter(status=Table.Status.AVAILABLE)
        if not tables.exists():
            available_tables = Table.objects.filter(
                floor__branch=reservation.branch,
                status=Table.Status.AVAILABLE,
                capacity__gte=reservation.guest_count,
                is_active=True,
            ).order_by("capacity")
            if available_tables.exists():
                best_table = available_tables.first()
                reservation.tables.add(best_table)
                best_table.status = Table.Status.RESERVED
                best_table.save(update_fields=["status"])

        reservation.tables.all().update(status=Table.Status.RESERVED)
        reservation.status = Reservation.Status.CONFIRMED
        reservation.confirmed_at = timezone.now()
        reservation.save(update_fields=["status", "confirmed_at"])
        return reservation

    @staticmethod
    @transaction.atomic
    def cancel_reservation(reservation_id, reason=""):
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        if reservation.status in [Reservation.Status.COMPLETED, Reservation.Status.CANCELLED]:
            raise ValueError("Reservation is already completed or cancelled.")
        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.cancellation_reason = reason
        reservation.save(update_fields=["status", "cancelled_at", "cancellation_reason"])
        reservation.tables.filter(status=Table.Status.RESERVED).update(status=Table.Status.AVAILABLE)
        return reservation

    @staticmethod
    @transaction.atomic
    def mark_seated(reservation_id):
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        if reservation.status not in [Reservation.Status.CONFIRMED, Reservation.Status.PENDING]:
            raise ValueError("Only confirmed or pending reservations can be seated.")

        tables = reservation.tables.all()
        if tables.exists():
            tables.update(status=Table.Status.OCCUPIED)
            for table in tables:
                TableSession.objects.get_or_create(
                    table=table,
                    status=TableSession.Status.OPEN,
                    defaults={"opened_at": timezone.now(), "notes": f"Reservation: {reservation.customer.name}"},
                )

        reservation.status = Reservation.Status.SEATED
        reservation.seated_at = timezone.now()
        reservation.save(update_fields=["status", "seated_at"])
        return reservation
