from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.permissions import group_required

from .models import MenuItem, MenuCategory
from .forms import MenuItemForm, MenuCategoryForm
from .services import MenuService


@group_required(
    "Admin",
    "Manager",
    "Cashier",
    "Kitchen",
)
def menu_list(request):

    items = MenuItem.objects.select_related(
        "category"
    ).all()

    return render(
        request,
        "menu/menu_list.html",
        {
            "items": items
        }
    )


@group_required("Admin", "Manager")
def create_menu_item(request):

    if request.method == "POST":

        form = MenuItemForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Menu item created successfully."
            )

            return redirect("menu_list")

    else:
        form = MenuItemForm()

    return render(
        request,
        "menu/create_menu_item.html",
        {
            "form": form
        }
    )


@group_required("Admin", "Manager")
def edit_menu_item(request, item_id):

    item = get_object_or_404(
        MenuItem,
        id=item_id
    )

    if request.method == "POST":

        form = MenuItemForm(
            request.POST,
            instance=item
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Menu item updated."
            )

            return redirect("menu_list")

    else:
        form = MenuItemForm(instance=item)

    return render(
        request,
        "menu/edit_menu_item.html",
        {
            "form": form,
            "item": item
        }
    )


@group_required("Admin", "Manager")
def toggle_item_availability(request, item_id):

    item = get_object_or_404(
        MenuItem,
        id=item_id
    )

    MenuService.toggle_item_availability(item)

    messages.success(
        request,
        "Item status updated."
    )

    return redirect("menu_list")


@group_required("Admin", "Manager")
def category_list(request):

    categories = MenuCategory.objects.all()

    return render(
        request,
        "menu/category_list.html",
        {
            "categories": categories
        }
    )


@group_required("Admin", "Manager")
def create_category(request):

    if request.method == "POST":

        form = MenuCategoryForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Category created."
            )

            return redirect("category_list")

    else:
        form = MenuCategoryForm()

    return render(
        request,
        "menu/create_category.html",
        {
            "form": form
        }
    )


@group_required("Admin", "Manager")
def edit_category(request, category_id):

    category = get_object_or_404(
        MenuCategory,
        id=category_id
    )

    if request.method == "POST":

        form = MenuCategoryForm(
            request.POST,
            instance=category
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Category updated."
            )

            return redirect("category_list")

    else:
        form = MenuCategoryForm(instance=category)

    return render(
        request,
        "menu/edit_category.html",
        {
            "form": form,
            "category": category
        }
    )


@group_required("Admin", "Manager")
def toggle_category(request, category_id):

    category = get_object_or_404(
        MenuCategory,
        id=category_id
    )

    MenuService.toggle_category(category)

    messages.success(
        request,
        "Category status updated."
    )

    return redirect("category_list")
