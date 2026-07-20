import re
from django.utils.deprecation import MiddlewareMixin
from .models import AuditService


class AuditMiddleware(MiddlewareMixin):
    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
    EXEMPT_PATHS = (
        re.compile(r"^/static/"),
        re.compile(r"^/media/"),
        re.compile(r"^/admin/"),
        re.compile(r"^/api/auth/"),
    )

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in self.SAFE_METHODS:
            return None
        for pattern in self.EXEMPT_PATHS:
            if pattern.match(request.path):
                return None
        if not request.user or not request.user.is_authenticated:
            return None
        entity_type = request.resolver_match.app_name or "unknown"
        action_map = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        action = action_map.get(request.method, request.method)
        AuditService.log(
            user=request.user,
            action=action,
            entity_type=entity_type,
            entity_id=view_kwargs.get("pk", "") or view_kwargs.get("id", ""),
            details={"path": request.path, "method": request.method},
            request=request,
        )
        return None
