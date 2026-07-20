from django.shortcuts import render
from django.db.models import Count
from core.permissions import group_required
from .models import AuditLog
from organisation.models import Branch


@group_required("Admin")
def audit_log_list(request):
    action = request.GET.get("action")
    entity_type = request.GET.get("entity_type")
    logs = AuditLog.objects.select_related("user").all().order_by("-created_at")
    if action:
        logs = logs.filter(action=action)
    if entity_type:
        logs = logs.filter(entity_type=entity_type)

    action_counts = AuditLog.objects.values("action").annotate(count=Count("id")).order_by("-count")
    entity_counts = AuditLog.objects.values("entity_type").annotate(count=Count("id")).order_by("-count")

    context = {
        "logs": logs[:200],
        "action_counts": action_counts,
        "entity_counts": entity_counts,
        "selected_action": action,
        "selected_entity": entity_type,
    }
    return render(request, "auditlog/list.html", context)
