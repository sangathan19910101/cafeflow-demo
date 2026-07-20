import json
from django.db import models
from django.contrib.auth import get_user_model


class AuditLog(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{user_str} - {self.action} - {self.entity_type} ({self.created_at})"


class AuditService:
    @staticmethod
    def log(user, action, entity_type, entity_id="", details=None, request=None):
        ip = None
        if request:
            ip = request.META.get("REMOTE_ADDR")
        AuditLog.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details or {},
            ip_address=ip,
        )
