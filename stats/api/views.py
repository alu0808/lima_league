from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.utils.authentication import DeviceTokenAuthentication
from config.responses import ok
from stats.api.models import PlayerMatchStat
from stats.api.serializers import PlayerMatchStatSerializer, StatsSummarySerializer


class MyStatsSummaryView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = PlayerMatchStat.objects.filter(user=request.user)
        data = StatsSummarySerializer.from_queryset(qs)
        return ok(data, message="Resumen de estadísticas")


class MyMatchStatsView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (PlayerMatchStat.objects
              .select_related("match")
              .filter(user=request.user)
              .order_by("-match__start_at", "-id"))
        data = PlayerMatchStatSerializer(qs, many=True).data
        return ok(data, message="Estadísticas por partido")
