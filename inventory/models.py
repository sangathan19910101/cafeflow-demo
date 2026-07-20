from django.db import models
from core.models import BaseModel
from organisation.models import Branch
from menu.models import MenuItem


class StockCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Stock Categories"

    def __str__(self):
        return self.name


class StockUnit(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class InventoryItem(BaseModel):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        StockCategory,
        on_delete=models.PROTECT,
        related_name="items",
    )
    unit = models.ForeignKey(
        StockUnit,
        on_delete=models.PROTECT,
        related_name="items",
    )
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Inventory Items"

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.low_stock_threshold


class MenuItemRecipe(BaseModel):
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="recipes",
    )
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="recipes",
    )
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["menu_item__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "inventory_item"],
                name="unique_recipe_item",
            )
        ]

    def __str__(self):
        return f"{self.menu_item.name} -> {self.quantity_required} x {self.inventory_item.name}"


class StockMovement(BaseModel):
    class MovementType(models.TextChoices):
        IN = "IN", "Stock In"
        OUT = "OUT", "Stock Out"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        WASTAGE = "WASTAGE", "Wastage"
        TRANSFER = "TRANSFER", "Transfer"

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} x {self.item.name}"


class StockTransfer(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="transfers")
    from_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="transfers_out")
    to_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="transfers_in")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, related_name="transfer_requests")
    approved_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="transfer_approvals")
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transfer {self.item.name}: {self.from_branch.name} -> {self.to_branch.name}"
