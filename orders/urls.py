from django.urls import path
from .views import (
    create_order,
    order_detail,
    add_order_item,
    submit_order,
    reject_order,
    accept_order,
    cancel_order,
    order_list,
)
urlpatterns = [
    path("create/<uuid:session_id>/", create_order, name="create_order"),
    path("<uuid:order_id>/", order_detail, name="order_detail"),
    path(
        "<uuid:order_id>/add-item/",
        add_order_item,
        name="add_order_item"),
    path(
        "<uuid:order_id>/submit/",
        submit_order,
        name="submit_order",
    ),
    path(
        "<uuid:order_id>/accept/",
        accept_order,
        name="accept_order",
    ),

    path(
        "<uuid:order_id>/reject/",
        reject_order,
        name="reject_order",
    ),
    path(
        "<uuid:order_id>/cancel/",
        cancel_order,
        name="cancel_order",
    ),
    path(
        "",
        order_list,
        name="order_list",
    ),

]
