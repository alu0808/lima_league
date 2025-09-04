# matches/serializers.py
from datetime import timezone as dt_timezone
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from accounts.api.models import User
from matches.api.models import Match, Location, MatchFAQ, MatchRecommendation, Enrollment

DAY_NAMES_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def to_utc(dt):
    if dt is None:
        return None
    # Asegura que el datetime está en UTC (aunque ya viene aware en UTC con USE_TZ)
    return timezone.localtime(dt, dt_timezone.utc)


def date_label_utc(start_at_utc):
    today = (timezone.now() - timedelta(hours=5)).date()
    d = start_at_utc.date()
    if d == today: return "Hoy"
    if d == (today + timezone.timedelta(days=1)): return "Mañana"
    return ""


class LocationSerializer(serializers.ModelSerializer):
    district = serializers.CharField(source="district.name")
    address = serializers.CharField()
    maps_url = serializers.CharField()
    field_name = serializers.CharField()

    class Meta:
        model = Location
        fields = ("district", "address", "maps_url", "field_name")


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchFAQ
        fields = ("question", "answer")


class RecommendationSerializer(serializers.ModelSerializer):
    text = serializers.CharField()

    class Meta:
        model = MatchRecommendation
        fields = ("text",)


class PlayerMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    position = serializers.CharField(source="position.name", default=None)
    dominant_foot = serializers.CharField(source="dominant_foot.name", default=None)

    class Meta:
        model = User
        fields = ("full_name", "position", "dominant_foot", "photo")

    def get_full_name(self, obj):
        return f"{(obj.first_name or '').strip()} {(obj.last_name or '').strip()}".strip() or obj.email



class UpcomingMatchSerializer(serializers.ModelSerializer):
    place = LocationSerializer(source="location")
    date = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    date_tag = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    button_text = serializers.CharField()
    photo = serializers.CharField(source="image_url", allow_null=True)
    info = serializers.SerializerMethodField()
    considerations = serializers.SerializerMethodField()
    faqs = FAQSerializer(many=True, read_only=True)
    registered_players = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = (
            "id",
            "place",
            "date", "day", "date_tag", "time",
            "button_text",
            "photo",
            "info",
            "considerations",
            "faqs",
            "registered_players",
        )

    # ---- helpers de formato ----
    def get_date(self, obj):
        dt = to_utc(obj.start_at)
        return dt.strftime("%d/%m/%Y")

    def get_day(self, obj):
        dt = to_utc(obj.start_at)
        return DAY_NAMES_ES[dt.weekday()]

    def get_date_tag(self, obj):
        return date_label_utc(obj.start_at)

    def get_time(self, obj):
        dt = to_utc(obj.start_at)
        return dt.strftime("%I:%M%p").lower()  # "11:00pm" si en BD es 23:00+00

    def get_info(self, obj):
        enrolled = Enrollment.objects.filter(match=obj, is_active=True).count()
        available = max(0, obj.capacity - enrolled)
        price_val = obj.price_amount
        price_label = f"S/ {int(price_val) if price_val == int(price_val) else price_val}"
        return {
            "price": price_label,
            "game_time": f"{obj.duration_minutes} minutos",
            "total_slots": obj.capacity,
            "signed_players": enrolled,
            "available_slots": available,
        }

    def get_considerations(self, obj):
        return {"recommendations": list(obj.recommendations.values_list("text", flat=True))}

    def get_registered_players(self, obj):
        users = (User.objects
                 .filter(match_enrollments__match=obj, match_enrollments__is_active=True)
                 .select_related("position", "dominant_foot")
                 .distinct())
        return PlayerMiniSerializer(users, many=True).data
