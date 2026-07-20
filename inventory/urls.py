from django.urls import path
from .views import inventory_list, inventory_detail, restock_item, create_inventory_item, category_list, create_category, unit_list, create_unit

urlpatterns = [
    path("", inventory_list, name="inventory_list"),
    path("create/", create_inventory_item, name="create_inventory_item"),
    path("categories/", category_list, name="inventory_category_list"),
    path("categories/create/", create_category, name="inventory_category_create"),
    path("units/", unit_list, name="inventory_unit_list"),
    path("units/create/", create_unit, name="inventory_unit_create"),
    path("<uuid:item_id>/", inventory_detail, name="inventory_detail"),
    path("<uuid:item_id>/restock/", restock_item, name="inventory_restock"),
]
