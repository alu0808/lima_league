# promos/api/serializers.py
from rest_framework import serializers

from promos.api.models import Banner, Sponsor


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.CharField(source="image_url")

    class Meta:
        model = Banner
        fields = ("image", "title", "description", "path", "order", "is_active")


class SponsorSerializer(serializers.ModelSerializer):
    image = serializers.CharField(source="image_url")

    class Meta:
        model = Sponsor
        fields = ("title", "image", "order", "is_active")
