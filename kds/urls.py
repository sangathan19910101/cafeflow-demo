from django.urls import path
from .views import kds_dashboard, start_preparing, mark_ready, mark_served

urlpatterns = [
    path("", kds_dashboard, name="kds_dashboard"),
    path("<uuid:entry_id>/start/", start_preparing, name="kds_start"),
    path("<uuid:entry_id>/ready/", mark_ready, name="kds_ready"),
    path("<uuid:entry_id>/served/", mark_served, name="kds_served"),
]
