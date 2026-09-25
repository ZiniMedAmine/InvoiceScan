"""Root URL configuration of the InvoiceScan+ project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("invoiceScanApp.urls")),
]

# Serve uploaded files during local development (no-op when DEBUG is off).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
