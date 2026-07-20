from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from core.permissions import group_required
from .models import InventoryItem, StockMovement, StockCategory, StockUnit
from .services import InventoryService


@group_required("Admin", "Manager")
def inventory_list(request):
    branch_id = request.GET.get("branch")
    category_id = request.GET.get("category")
    items = InventoryItem.objects.select_related("category", "unit", "branch").filter(is_active=True)
    if branch_id:
        items = items.filter(branch_id=branch_id)
    if category_id:
        items = items.filter(category_id=category_id)
    low_stock = [i for i in items if i.is_low_stock]
    from organisation.models import Branch
    return render(request, "inventory/list.html", {
        "items": items,
        "low_stock_count": len(low_stock),
        "categories": StockCategory.objects.all(),
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def inventory_detail(request, item_id):
    item = get_object_or_404(InventoryItem.objects.select_related("category", "unit", "branch"), pk=item_id)
    movements = StockMovement.objects.filter(item=item).order_by("-created_at")[:50]
    return render(request, "inventory/detail.html", {
        "item": item,
        "movements": movements,
    })


@group_required("Admin", "Manager")
def restock_item(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)
    if request.method == "POST":
        try:
            qty = Decimal(request.POST.get("quantity", 0))
            notes = request.POST.get("notes", "")
            InventoryService.restock(item_id=item_id, quantity=qty, notes=notes, user=request.user)
            messages.success(request, f"Restocked {qty} {item.unit.abbreviation} of {item.name}.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("inventory_detail", item_id=item_id)
    return render(request, "inventory/restock.html", {"item": item})


@group_required("Admin", "Manager")
def create_inventory_item(request):
    if request.method == "POST":
        from .models import InventoryItem, StockCategory, StockUnit
        from organisation.models import Branch
        try:
            name = request.POST["name"]
            category_id = request.POST["category"]
            unit_id = request.POST["unit"]
            branch_id = request.POST["branch"]
            quantity = float(request.POST.get("quantity_in_stock", 0))
            threshold = float(request.POST.get("low_stock_threshold", 10))
            cost = float(request.POST.get("unit_cost", 0))
            item = InventoryItem.objects.create(
                name=name, category_id=category_id, unit_id=unit_id,
                branch_id=branch_id, quantity_in_stock=quantity,
                low_stock_threshold=threshold, unit_cost=cost,
            )
            messages.success(request, f"Inventory item '{item.name}' created.")
            return redirect("inventory_list")
        except (KeyError, ValueError) as e:
            messages.error(request, f"Error: {e}")
    from .models import StockCategory, StockUnit
    from organisation.models import Branch
    return render(request, "inventory/create_item.html", {
        "categories": StockCategory.objects.all(),
        "units": StockUnit.objects.all(),
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def category_list(request):
    categories = StockCategory.objects.all().order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


@group_required("Admin", "Manager")
def create_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            StockCategory.objects.create(name=name, description=description)
            messages.success(request, f"Stock category '{name}' created.")
            return redirect("inventory_category_list")
        messages.error(request, "Name is required.")
    return render(request, "inventory/create_category.html")


@group_required("Admin", "Manager")
def unit_list(request):
    units = StockUnit.objects.all().order_by("name")
    return render(request, "inventory/unit_list.html", {"units": units})


@group_required("Admin", "Manager")
def create_unit(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        abbreviation = request.POST.get("abbreviation", "").strip()
        if name and abbreviation:
            StockUnit.objects.create(name=name, abbreviation=abbreviation)
            messages.success(request, f"Stock unit '{name}' created.")
            return redirect("inventory_unit_list")
        messages.error(request, "Name and abbreviation are required.")
    return render(request, "inventory/create_unit.html")
