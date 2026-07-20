from django.contrib import admin
from .models import KDSDisplay


@admin.register(KDSDisplay)
class KDSDisplayAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "branch", "status", "priority", "created_at")
    list_filter = ("status", "branch")
