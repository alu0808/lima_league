# payments/serializers.py
from rest_framework import serializers

from payments.api.models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    match_identifier = serializers.UUIDField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("public_id", "status", "preference_id", "init_point", "sandbox_init_point")
