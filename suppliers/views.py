from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from core.permissions import group_required
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt


@group_required("Admin", "Manager")
def create_supplier(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        company = request.POST.get("company", "")
        email = request.POST.get("email", "")
        address = request.POST.get("address", "")
        payment_terms = request.POST.get("payment_terms", "")
        if name and phone:
            supplier = Supplier.objects.create(name=name, phone=phone, company=company, email=email, address=address, payment_terms=payment_terms)
            messages.success(request, f"Supplier '{supplier.name}' created.")
            return redirect("supplier_list")
        messages.error(request, "Name and phone are required.")
    return render(request, "suppliers/create_supplier.html")


@group_required("Admin", "Manager")
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    if request.method == "POST":
        supplier.name = request.POST.get("name", supplier.name)
        supplier.phone = request.POST.get("phone", supplier.phone)
        supplier.company = request.POST.get("company", "")
        supplier.email = request.POST.get("email", "")
        supplier.address = request.POST.get("address", "")
        supplier.payment_terms = request.POST.get("payment_terms", "")
        supplier.save()
        messages.success(request, "Supplier updated.")
        return redirect("supplier_detail", supplier_id=supplier.id)
    return render(request, "suppliers/edit_supplier.html", {"supplier": supplier})


@group_required("Admin", "Manager")
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by("name")
    status = request.GET.get("status")
    if status:
        suppliers = suppliers.filter(status=status)
    return render(request, "suppliers/supplier_list.html", {"suppliers": suppliers})


@group_required("Admin", "Manager")
def supplier_detail(request, supplier_id):
    supplier = get_object_or_404(
        Supplier.objects.prefetch_related("contacts", "pricing", "pricing__item"),
        pk=supplier_id,
    )
    pos = PurchaseOrder.objects.filter(supplier=supplier).order_by("-order_date")[:20]
    return render(request, "suppliers/supplier_detail.html", {"supplier": supplier, "pos": pos})


@group_required("Admin", "Manager")
def purchase_order_list(request):
    pos = PurchaseOrder.objects.select_related("supplier", "branch", "ordered_by").all().order_by("-order_date")
    status = request.GET.get("status")
    if status:
        pos = pos.filter(status=status)
    return render(request, "suppliers/po_list.html", {"pos": pos})


@group_required("Admin", "Manager")
def create_purchase_order(request):
    from inventory.models import InventoryItem
    if request.method == "POST":
        supplier_id = request.POST.get("supplier")
        branch_id = request.POST.get("branch")
        item_ids = request.POST.getlist("item")
        quantities = request.POST.getlist("quantity")
        prices = request.POST.getlist("unit_price")
        items_data = []
        for i, item_id in enumerate(item_ids):
            if item_id:
                try:
                    qty = quantities[i] if i < len(quantities) and quantities[i] else "1"
                    prc = prices[i] if i < len(prices) and prices[i] else "0"
                except IndexError:
                    qty, prc = "1", "0"
                items_data.append({
                    "item_id": item_id,
                    "quantity": float(qty),
                    "unit_price": float(prc),
                })
        if supplier_id and branch_id and items_data:
            from .services import SupplierService
            try:
                po = SupplierService.create_purchase_order(supplier_id, branch_id, items_data, request.user)
                messages.success(request, f"Purchase Order {po.po_number} created.")
                return redirect("po_detail", po_id=po.id)
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Supplier, branch, and at least one item are required.")
    from organisation.models import Branch
    return render(request, "suppliers/create_po.html", {
        "suppliers": Supplier.objects.filter(status=Supplier.Status.ACTIVE),
        "branches": Branch.objects.filter(is_active=True),
        "items": InventoryItem.objects.filter(is_active=True).select_related("category", "unit"),
    })


@group_required("Admin", "Manager")
def purchase_order_detail(request, po_id):
    po = get_object_or_404(
        PurchaseOrder.objects.select_related("supplier", "branch", "ordered_by").prefetch_related("items__item"),
        pk=po_id,
    )
    receipts = GoodsReceipt.objects.filter(purchase_order=po).prefetch_related("items__po_item__item")
    return render(request, "suppliers/po_detail.html", {"po": po, "receipts": receipts})


@group_required("Admin", "Manager")
def confirm_po(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    if request.method == "POST":
        po.status = PurchaseOrder.Status.CONFIRMED
        po.confirmed_at = timezone.now()
        po.save(update_fields=["status", "confirmed_at"])
        messages.success(request, f"PO {po.po_number} confirmed.")
    return redirect("po_detail", po_id=po_id)


@group_required("Admin", "Manager")
def receive_po(request, po_id):
    po = get_object_or_404(
        PurchaseOrder.objects.select_related("supplier").prefetch_related("items__item"),
        pk=po_id,
    )
    if request.method == "POST":
        from .services import SupplierService
        from decimal import Decimal
        try:
            received_items = []
            for po_item in po.items.all():
                qty_key = f"qty_{po_item.id}"
                if qty_key in request.POST:
                    qty = Decimal(request.POST[qty_key] or "0")
                    if qty > 0:
                        received_items.append({
                            "po_item_id": po_item.id,
                            "quantity_received": qty,
                        })
            if received_items:
                receipt = SupplierService.receive_goods(po.id, received_items, request.user)
                messages.success(request, f"Goods receipt created. PO status: {po.get_status_display()}.")
            else:
                messages.error(request, "Please enter quantities to receive.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect("po_detail", po_id=po_id)
    return render(request, "suppliers/receive_po.html", {"po": po})
