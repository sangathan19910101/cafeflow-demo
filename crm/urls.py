from django.urls import path
from .views import (
    customer_list, customer_detail, create_customer, edit_customer, delete_customer,
    create_segment, segment_list, feedback_list, add_feedback,
    loyalty_list, enroll_loyalty, create_loyalty_program, edit_loyalty_program,
    loyalty_transactions, send_communication, populate_segment, customer_communications,
)

urlpatterns = [
    path("customers/create/", create_customer, name="create_customer"),
    path("customers/", customer_list, name="customer_list"),
    path("customers/<uuid:customer_id>/edit/", edit_customer, name="edit_customer"),
    path("customers/<uuid:customer_id>/delete/", delete_customer, name="delete_customer"),
    path("customers/<uuid:customer_id>/feedback/", add_feedback, name="add_feedback"),
    path("customers/<uuid:customer_id>/loyalty/", enroll_loyalty, name="enroll_loyalty"),
    path("customers/<uuid:customer_id>/communications/", customer_communications, name="customer_communications"),
    path("customers/<uuid:customer_id>/", customer_detail, name="customer_detail"),
    path("segments/create/", create_segment, name="create_segment"),
    path("segments/", segment_list, name="segment_list"),
    path("segments/<uuid:segment_id>/populate/", populate_segment, name="populate_segment"),
    path("feedback/", feedback_list, name="feedback_list"),
    path("loyalty/", loyalty_list, name="loyalty_list"),
    path("loyalty/create/", create_loyalty_program, name="create_loyalty_program"),
    path("loyalty/<uuid:program_id>/edit/", edit_loyalty_program, name="edit_loyalty_program"),
    path("loyalty/transactions/", loyalty_transactions, name="loyalty_transactions"),
    path("loyalty/transactions/<uuid:customer_id>/", loyalty_transactions, name="customer_loyalty_transactions"),
    path("communications/send/", send_communication, name="send_communication"),
    path("communications/send/<uuid:customer_id>/", send_communication, name="send_customer_communication"),
]
