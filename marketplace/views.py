from django.shortcuts import render
from core.permissions import group_required
from .models import ConnectedApp, ApiKey


@group_required("Admin")
def marketplace_home(request):
    apps = ConnectedApp.objects.all()
    api_keys = ApiKey.objects.select_related("user").all()
    return render(request, "marketplace/home.html", {"apps": apps, "api_keys": api_keys})
