from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("core.urls")),
    path("api/v1/auth/", include("accounts.auth_urls")),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("organizations.urls")),
    path("api/v1/", include("dashboard.urls")),
    path("api/v1/", include("roadmaps.urls")),
    path("api/v1/", include("coding.urls")),
    path("api/v1/", include("study_workspace.urls")),
    path("api/v1/", include("knowledge_base.urls")),
    path("api/v1/", include("billing.urls")),
    path("api/v1/", include("goals.urls")),
]
