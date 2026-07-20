from django.db import transaction
from django.utils import timezone
from menu.models import MenuItem
from .models import InventoryItem, StockMovement, MenuItemRecipe


class InventoryService:
    @staticmethod
    @transaction.atomic
    def consume_ingredients(menu_item: MenuItem, quantity=1):
        recipes = MenuItemRecipe.objects.filter(menu_item=menu_item).select_related("inventory_item")
        if not recipes.exists():
            return
        for recipe in recipes:
            item = InventoryItem.objects.select_for_update().get(pk=recipe.inventory_item.pk)
            required = recipe.quantity_required * quantity
            if item.quantity_in_stock < required:
                raise ValueError(f"Insufficient stock: {item.name} (need {required}, have {item.quantity_in_stock})")
            item.quantity_in_stock -= required
            item.save(update_fields=["quantity_in_stock"])
            StockMovement.objects.create(
                item=item,
                movement_type=StockMovement.MovementType.OUT,
                quantity=required,
                notes=f"Consumed for {menu_item.name} x{quantity}",
            )

    @staticmethod
    @transaction.atomic
    def restock(item_id, quantity, notes="", user=None):
        item = InventoryItem.objects.select_for_update().get(pk=item_id)
        item.quantity_in_stock += quantity
        item.save(update_fields=["quantity_in_stock"])
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.MovementType.IN,
            quantity=quantity,
            notes=notes,
            recorded_by=user,
        )
        return item

    @staticmethod
    @transaction.atomic
    def adjust_stock(item_id, new_quantity, notes="", user=None):
        item = InventoryItem.objects.select_for_update().get(pk=item_id)
        diff = new_quantity - item.quantity_in_stock
        item.quantity_in_stock = new_quantity
        item.save(update_fields=["quantity_in_stock"])
        mt = StockMovement.MovementType.ADJUSTMENT
        StockMovement.objects.create(
            item=item,
            movement_type=mt,
            quantity=diff,
            notes=notes,
            recorded_by=user,
        )
        return item
