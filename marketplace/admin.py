from django.contrib import admin
from .models import ConnectedApp, ApiKey


@admin.register(ConnectedApp)
class ConnectedAppAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "app_type", "is_active")
    list_filter = ("app_type", "is_active")


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_active", "last_used_at", "expires_at")
    list_filter = ("is_active",)
