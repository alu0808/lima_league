from django.db.models import Sum
from rest_framework import serializers

from stats.api.models import PlayerMatchStat


class PlayerMatchStatSerializer(serializers.ModelSerializer):
    match_id = serializers.IntegerField(source="match.id", read_only=True)
    match_identifier = serializers.UUIDField(source="match.match_identifier", read_only=True)
    match_title = serializers.CharField(source="match.title", read_only=True)
    match_start_at = serializers.DateTimeField(source="match.start_at", read_only=True)

    class Meta:
        model = PlayerMatchStat
        fields = (
            "match_id", "match_identifier", "match_title", "match_start_at",
            "goals", "is_winner", "is_mvp",
        )


class StatsSummarySerializer(serializers.Serializer):
    matches = serializers.IntegerField()
    wins = serializers.IntegerField()
    goals = serializers.IntegerField()
    mvps = serializers.IntegerField()

    @staticmethod
    def from_queryset(qs):
        return {
            "matches": qs.count(),
            "wins": qs.filter(is_winner=True).count(),
            "goals": qs.aggregate(total=Sum("goals"))["total"] or 0,
            "mvps": qs.filter(is_mvp=True).count(),
        }
