from django.db import transaction
from django.utils import timezone

from organisation.models import Table, TableSession


class SessionService:

    @staticmethod
    @transaction.atomic
    def start_session(table: Table):

        table = (
            Table.objects
            .select_for_update()
            .get(pk=table.pk)
        )

        if table.status != Table.Status.AVAILABLE:
            raise ValueError(
                "Session can only be started on available tables."
            )

        existing = TableSession.objects.filter(
            table=table,
            status=TableSession.Status.OPEN,
        ).exists()

        if existing:
            raise ValueError(
                "Session already active for this table."
            )

        session = TableSession.objects.create(
            table=table,
            status=TableSession.Status.OPEN,
            opened_at=timezone.now(),
        )

        table.status = Table.Status.OCCUPIED

        table.save(update_fields=["status"])

        return session
