from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

handler403 = "core.views.permission_denied_view"


def home(request):
    return HttpResponse("CafeFlow POS is running.")


urlpatterns = [
    path('', include('dashboard.urls')),
    path('', include('organisation.urls')),
    path("sessions/", include("operations.urls")),
    path("orders/", include("orders.urls")),
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("billing/", include("billing.urls")),
    path("menu/", include("menu.urls")),
    path("analytics/", include("analytics.urls")),
    path("kds/", include("kds.urls")),
    path("inventory/", include("inventory.urls")),
    path("coupons/", include("coupons.urls")),
    path("reservations/", include("reservations.urls")),
    path("audit-logs/", include("auditlog.urls")),
    path("crm/", include("crm.urls")),
    path("staff/", include("staff.urls")),
    path("payroll/", include("payroll.urls")),
    path("suppliers/", include("suppliers.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("reports/", include("reports.urls")),
    path("api/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
