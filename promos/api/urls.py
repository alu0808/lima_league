# promos/api/urls.py
from django.urls import path

from promos.api.views import PublicPromosView

urlpatterns = [
    path("promos", PublicPromosView.as_view(), name="public-promos"),
]
