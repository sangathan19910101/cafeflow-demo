from django.contrib import admin
from .models import Branch, Floor, Table


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "rows", "columns", "is_active")
    list_filter = ("branch", "is_active")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name", "floor", "capacity", "shape", "status", "is_active")
    list_filter = ("status", "shape", "is_active", "floor__branch")
