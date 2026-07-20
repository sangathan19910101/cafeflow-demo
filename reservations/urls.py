from django.urls import path
from .views import (
    reservation_list, create_reservation, confirm_reservation, cancel_reservation,
    mark_seated, notify_waitlist, customer_lookup, available_tables,
)

urlpatterns = [
    path("create/", create_reservation, name="create_reservation"),
    path("customers/lookup/", customer_lookup, name="customer_lookup"),
    path("tables/available/", available_tables, name="available_tables"),
    path("", reservation_list, name="reservation_list"),
    path("<uuid:reservation_id>/confirm/", confirm_reservation, name="confirm_reservation"),
    path("<uuid:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
    path("<uuid:reservation_id>/seat/", mark_seated, name="mark_seated"),
    path("waitlist/<uuid:entry_id>/notify/", notify_waitlist, name="notify_waitlist"),
]
