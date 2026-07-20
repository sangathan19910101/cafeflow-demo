from django.urls import path
from .views import coupon_list, create_coupon

urlpatterns = [
    path("create/", create_coupon, name="create_coupon"),
    path("", coupon_list, name="coupon_list"),
]
