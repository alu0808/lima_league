# accounts/urls.py
from django.urls import path

from accounts.api.views import (
    RegisterView, LoginView, LogoutView, LogoutAllView,
    ChangePasswordView, EditDataView, RegistrationCatalogView, DistrictsByCityView, MyTeamHistoryView
)

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/logout-all", LogoutAllView.as_view(), name="auth-logout-all"),

    path("profile", EditDataView.as_view(), name="profile-edit"),
    path("profile/change-password", ChangePasswordView.as_view(), name="profile-change-password"),

    path("profile/teams", MyTeamHistoryView.as_view(), name="profile-teams"),

    path("catalogs/registration", RegistrationCatalogView.as_view(), name="catalogs-registration"),
    path("catalogs/districts", DistrictsByCityView.as_view(), name="catalogs-districts"),
]
