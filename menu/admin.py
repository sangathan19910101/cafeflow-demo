from django.contrib import admin
from .models import MenuCategory, MenuItem, ModifierGroup, Modifier, TaxCategory


@admin.register(TaxCategory)
class TaxCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "is_active")
    list_filter = ("is_active",)


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "min_selections", "max_selections", "is_required", "is_active")
    list_filter = ("is_required", "is_active")


@admin.register(Modifier)
class ModifierAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "price_adjustment", "is_default", "is_active")
    list_filter = ("group", "is_active")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "cost_price", "is_available", "is_featured", "preparation_time")
    list_filter = ("category", "is_available", "is_featured")
    search_fields = ("name", "barcode")
    filter_horizontal = ("modifier_groups",)
