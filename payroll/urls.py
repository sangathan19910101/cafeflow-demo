from django.urls import path
from .views import (
    payroll_periods, payslip_list, payslip_detail, process_payroll,
    create_leave_request, leave_requests, approve_leave, reject_leave,
    create_payroll_period, leave_type_list, create_leave_type,
)

urlpatterns = [
    path("periods/create/", create_payroll_period, name="create_payroll_period"),
    path("periods/", payroll_periods, name="payroll_periods"),
    path("periods/<uuid:period_id>/payslips/", payslip_list, name="payslip_list"),
    path("periods/<uuid:period_id>/process/", process_payroll, name="process_payroll"),
    path("payslips/<uuid:payslip_id>/", payslip_detail, name="payslip_detail"),
    path("leaves/create/", create_leave_request, name="create_leave_request"),
    path("leaves/types/create/", create_leave_type, name="create_leave_type"),
    path("leaves/types/", leave_type_list, name="leave_type_list"),
    path("leaves/", leave_requests, name="leave_requests"),
    path("leaves/<uuid:leave_id>/approve/", approve_leave, name="approve_leave"),
    path("leaves/<uuid:leave_id>/reject/", reject_leave, name="reject_leave"),
]
