from django.db import models
from django.db.models import Q

from core.models import BaseModel


class Branch(BaseModel):
    name = models.CharField(
        max_length=150,
        unique=True
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name


class Floor(BaseModel):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="floors",
    )

    name = models.CharField(max_length=100)

    rows = models.PositiveIntegerField(default=10)
    columns = models.PositiveIntegerField(default=10)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                name="unique_floor_per_branch",
            )
        ]

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class Table(BaseModel):

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        OCCUPIED = "OCCUPIED", "Occupied"
        CLEANING = "CLEANING", "Cleaning"

    class Shape(models.TextChoices):
        SQUARE = "SQUARE", "Square"
        ROUND = "ROUND", "Round"
        RECTANGLE = "RECTANGLE", "Rectangle"
        BOOTH = "BOOTH", "Booth"

    floor = models.ForeignKey(
        Floor,
        on_delete=models.PROTECT,
        related_name="tables",
    )

    name = models.CharField(
        max_length=50
    )

    capacity = models.PositiveIntegerField(
        default=4
    )

    shape = models.CharField(
        max_length=20,
        choices=Shape.choices,
        default=Shape.SQUARE,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    pos_x = models.PositiveIntegerField(
        default=0
    )

    pos_y = models.PositiveIntegerField(
        default=0
    )

    width = models.PositiveIntegerField(
        default=1
    )

    height = models.PositiveIntegerField(
        default=1
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["floor", "name"],
                name="unique_table_per_floor",
            )
        ]

    def __str__(self):
        return f"{self.floor.name} - {self.name}"


class TableSession(BaseModel):

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    table = models.ForeignKey(
        Table,
        on_delete=models.PROTECT,
        related_name="sessions",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(blank=True)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    is_billed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-opened_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["table"],
                condition=Q(status="OPEN"),
                name="unique_open_session_per_table",
            )
        ]

    def __str__(self):
        return f"{self.table.name} - {self.opened_at}"
