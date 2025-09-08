from django.urls import path

from stats.api.views import MyStatsSummaryView, MyMatchStatsView

urlpatterns = [
    path("stats/summary", MyStatsSummaryView.as_view(), name="stats-me-summary"),
    path("stats/matches", MyMatchStatsView.as_view(), name="stats-me-matches"),
]
