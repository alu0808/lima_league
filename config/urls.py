# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.api.urls")),
    path("api/", include("matches.api.urls")),
    path("api/", include("payments.api.urls")),
    path("api/", include("promos.api.urls")),
    path("api/", include("stats.api.urls")),
]