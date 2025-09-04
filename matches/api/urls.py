# matches/urls.py
from django.urls import path

from .views import UpcomingMatchesView, MatchDetailView, JoinMatchView, LeaveMatchView

urlpatterns = [
    path("matches/upcoming", UpcomingMatchesView.as_view(), name="auth-register"),
    path("matches/<int:match_id>", MatchDetailView.as_view(), name="auth-register"),
    path("matches/<int:match_id>/join", JoinMatchView.as_view(), name="auth-register"),
    path("matches/<int:match_id>/leave", LeaveMatchView.as_view(), name="auth-register"),
]
