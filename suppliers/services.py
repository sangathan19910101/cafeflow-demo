from django.db import transaction
from django.utils import timezone
from inventory.models import InventoryItem, StockMovement
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem, SupplierPricing


class SupplierService:
    @staticmethod
    @transaction.atomic
    def create_purchase_order(supplier_id, branch_id, items_data, user):
        from .models import Supplier
        supplier = Supplier.objects.get(pk=supplier_id)
        count = PurchaseOrder.objects.count()
        po_number = f"PO-{timezone.now():%Y%m%d}-{count + 1:04d}"

        po = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier_id=supplier_id,
            branch_id=branch_id,
            ordered_by=user,
        )

        subtotal = 0
        for item_data in items_data:
            inv_item = InventoryItem.objects.get(pk=item_data["item_id"])
            pricing = SupplierPricing.objects.filter(
                supplier=supplier, item=inv_item
            ).order_by("-is_preferred", "unit_price").first()

            unit_price = pricing.unit_price if pricing else item_data.get("unit_price", 0)
            qty = item_data["quantity"]
            line_total = unit_price * qty
            subtotal += line_total

            PurchaseOrderItem.objects.create(
                purchase_order=po,
                item=inv_item,
                quantity_ordered=qty,
                unit_price=unit_price,
                line_total=line_total,
            )

        po.subtotal = subtotal
        po.grand_total = subtotal + po.tax_amount + po.shipping_cost
        po.save(update_fields=["subtotal", "grand_total"])
        return po

    @staticmethod
    @transaction.atomic
    def receive_goods(po_id, received_items, user):
        po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
        if po.status not in [PurchaseOrder.Status.CONFIRMED, PurchaseOrder.Status.PARTIAL]:
            raise ValueError("PO must be confirmed before receiving goods.")

        receipt = GoodsReceipt.objects.create(
            purchase_order=po,
            received_by=user,
        )

        for ri in received_items:
            po_item = PurchaseOrderItem.objects.get(pk=ri["po_item_id"])
            qty = ri["quantity_received"]

            GoodsReceiptItem.objects.create(
                goods_receipt=receipt,
                po_item=po_item,
                quantity_received=qty,
                unit_price=po_item.unit_price,
            )

            po_item.quantity_received += qty
            po_item.save(update_fields=["quantity_received"])

            inv_item = po_item.item
            inv_item.quantity_in_stock += qty
            inv_item.save(update_fields=["quantity_in_stock"])

            StockMovement.objects.create(
                item=inv_item,
                movement_type=StockMovement.MovementType.IN,
                quantity=qty,
                notes=f"Received via PO {po.po_number}",
                recorded_by=user,
            )

        all_received = all(
            item.quantity_received >= item.quantity_ordered
            for item in po.items.all()
        )
        if all_received:
            po.status = PurchaseOrder.Status.RECEIVED
        else:
            po.status = PurchaseOrder.Status.PARTIAL
        po.save(update_fields=["status"])
        return receipt
