from django.urls import path
from .views import bill_list, pay_bill, bill_detail, online_payment, payment_success, payment_failed, print_bill, apply_coupon

urlpatterns = [
    path("", bill_list, name="bill_list"),
    path("<uuid:bill_id>/apply-coupon/", apply_coupon, name="apply_coupon"),
    path("pay/<uuid:bill_id>/", pay_bill, name="pay_bill"),
    path("<uuid:bill_id>/", bill_detail, name="bill_detail"),
    path("<uuid:bill_id>/pay-online/<str:gateway>/", online_payment, name="online_payment"),
    path("<uuid:bill_id>/payment-success/", payment_success, name="payment_success"),
    path("<uuid:bill_id>/payment-failed/", payment_failed, name="payment_failed"),
    path("<uuid:bill_id>/print/", print_bill, name="print_bill"),
]
