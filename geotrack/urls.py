from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # OpenAPI schema (raw JSON) — used by Swagger UI to render the docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI — main API documentation interface
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Fleet app endpoints
    path('api/', include('fleet.urls')),
]