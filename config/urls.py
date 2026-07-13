"""Root URL configuration"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("health", lambda _request: JsonResponse({"status": "ok"})),
    path("admin/", admin.site.urls),
    path("api/token", TokenObtainPairView.as_view(), name="token-obtain"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/", include("clinic.api.urls")),
    path("", include("clinic.web.urls")),
]
