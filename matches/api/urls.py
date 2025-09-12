# matches/urls.py
from django.urls import path

from .views import UpcomingMatchesView, MatchDetailView, JoinMatchView, LeaveMatchView, MatchesBoardView

urlpatterns = [
    path("matches/upcoming", UpcomingMatchesView.as_view(), name="matches-upcoming"),
    path("matches/board", MatchesBoardView.as_view(), name="matches-board"),
    path("matches/<uuid:match_identifier>", MatchDetailView.as_view(), name="matches-detail"),
    path("matches/<uuid:match_identifier>/join", JoinMatchView.as_view(), name="matches-join"),
    path("matches/<uuid:match_identifier>/leave", LeaveMatchView.as_view(), name="matches-leave"),
]
