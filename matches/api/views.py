# matches/views.py
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from accounts.utils.authentication import DeviceTokenAuthentication
from config.responses import ok, error
from matches.api.models import Match, MatchStatus
from matches.api.serializers import UpcomingMatchSerializer
from matches.services.enrollments import join_match, leave_match
from payments.api.models import Payment, PaymentStatus


class UpcomingMatchesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now() - timedelta(hours=5)
        qs = (Match.objects
              .select_related("location", "location__district")
              .prefetch_related("faqs", "recommendations")
              .filter(status=MatchStatus.PUBLISHED, start_at__gt=now)
              .order_by("start_at"))
        data = UpcomingMatchSerializer(qs, many=True).data
        return ok({"upcoming_matches": data}, message="Upcoming matches")


class MatchDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, match_identifier):
        m = (
            Match.objects
            .select_related("location", "location__district")
            .prefetch_related("faqs", "recommendations")
            .filter(match_identifier=match_identifier)
            .first()
        )
        if not m:
            return error("Match not found", status_code=status.HTTP_404_NOT_FOUND)
        data = UpcomingMatchSerializer(m).data
        return ok(data, message="Match")


class JoinMatchView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, match_identifier):
        m = get_object_or_404(Match, match_identifier=match_identifier)

        # Bloquea join si el usuario no tiene pago aprobado
        has_payment = Payment.objects.filter(
            user=request.user, match=m, status=PaymentStatus.APPROVED
        ).exists()

        if not has_payment:
            return error("Payment required", status_code=status.HTTP_402_PAYMENT_REQUIRED)

        try:
            payload = join_match(request.user, m.id)
        except Exception as e:
            return error(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        return ok(payload, message="Joined")


class LeaveMatchView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, match_identifier):
        m = get_object_or_404(Match, match_identifier=match_identifier)
        try:
            payload = leave_match(request.user, m.id)
        except Exception as e:
            return error(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        return ok(payload, message="Left")
