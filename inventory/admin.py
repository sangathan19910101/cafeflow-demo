from django.contrib import admin
from .models import StockCategory, StockUnit, InventoryItem, MenuItemRecipe, StockMovement


@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(StockUnit)
class StockUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "quantity_in_stock", "low_stock_threshold", "is_low_stock", "branch")
    list_filter = ("category", "branch", "is_active")


@admin.register(MenuItemRecipe)
class MenuItemRecipeAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "inventory_item", "quantity_required")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "created_at")
    list_filter = ("movement_type",)
