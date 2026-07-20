import uuid
from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel


class ConnectedApp(BaseModel):
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100, help_text="e.g., Swiggy, Zomato, Google")
    app_type = models.CharField(max_length=50, help_text="e.g., delivery, payment, accounting")
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    webhook_secret = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ApiKey(BaseModel):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="api_keys")
    permissions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.key[:16]}...)"
