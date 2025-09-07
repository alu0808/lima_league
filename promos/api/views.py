# promos/api/views.py
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.responses import ok
from promos.api.models import Banner, Sponsor
from promos.api.serializers import BannerSerializer, SponsorSerializer


class PublicPromosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        banners_qs = Banner.objects.filter(is_active=True).order_by("order", "id")
        sponsors_qs = Sponsor.objects.filter(is_active=True).order_by("order", "id")

        data = {
            "banners": BannerSerializer(banners_qs, many=True).data,
            "sponsors": SponsorSerializer(sponsors_qs, many=True).data,
        }

        return ok(data, message="Promos")
