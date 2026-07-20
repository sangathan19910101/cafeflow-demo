from django.urls import path

from .views import menu_list, create_menu_item, edit_menu_item, category_list, create_category, edit_category, toggle_category, toggle_item_availability

urlpatterns = [
    path(
        "",
        menu_list,
        name="menu_list",
    ),
    path(
        "create/",
        create_menu_item,
        name="create_menu_item",
    ),
    path(
        "<uuid:item_id>/edit/",
        edit_menu_item,
        name="edit_menu_item",
    ),
    path(
        "categories/",
        category_list,
        name="category_list",
    ),

    path(
        "categories/create/",
        create_category,
        name="create_category",
    ),

    path(
        "categories/<uuid:category_id>/edit/",
        edit_category,
        name="edit_category",
    ),

    path(
        "categories/<uuid:category_id>/toggle/",
        toggle_category,
        name="toggle_category",
    ),
    path(
        "<uuid:item_id>/toggle/",
        toggle_item_availability,
        name="toggle_item_availability",
    ),
]
