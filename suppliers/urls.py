from django.urls import path
from .views import create_supplier, edit_supplier, supplier_list, supplier_detail, purchase_order_list, purchase_order_detail, confirm_po, create_purchase_order, receive_po

urlpatterns = [
    path("suppliers/create/", create_supplier, name="create_supplier"),
    path("suppliers/<uuid:supplier_id>/edit/", edit_supplier, name="edit_supplier"),
    path("suppliers/", supplier_list, name="supplier_list"),
    path("suppliers/<uuid:supplier_id>/", supplier_detail, name="supplier_detail"),
    path("purchase-orders/create/", create_purchase_order, name="create_po"),
    path("purchase-orders/", purchase_order_list, name="po_list"),
    path("purchase-orders/<uuid:po_id>/", purchase_order_detail, name="po_detail"),
    path("purchase-orders/<uuid:po_id>/confirm/", confirm_po, name="confirm_po"),
    path("purchase-orders/<uuid:po_id>/receive/", receive_po, name="receive_po"),
]
