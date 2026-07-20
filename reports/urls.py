from django.urls import path
from .views import report_list, report_view, scheduled_reports, download_report, quick_report

urlpatterns = [
    path("", report_list, name="report_list"),
    path("quick/", quick_report, name="quick_report"),
    path("scheduled/", scheduled_reports, name="scheduled_reports"),
    path("<uuid:template_id>/download/", download_report, name="download_report"),
    path("<uuid:template_id>/", report_view, name="report_view"),
]
