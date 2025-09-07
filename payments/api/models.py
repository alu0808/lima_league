# payments/models.py
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    FAILED_CAPACITY = "failed_capacity", "Failed capacity"


class Payment(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    match = models.ForeignKey("matches.Match", on_delete=models.PROTECT, related_name="payments")

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="PEN")

    # Preference (Checkout Pro)
    preference_id = models.CharField(max_length=120, blank=True)
    init_point = models.URLField(max_length=1000, blank=True)
    sandbox_init_point = models.URLField(max_length=1000, blank=True)

    # Payment result
    mp_payment_id = models.CharField(max_length=120, blank=True)
    mp_status = models.CharField(max_length=50, blank=True)
    external_reference = models.CharField(max_length=64, db_index=True)  # atado a public_id

    status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["external_reference"]),
            models.Index(fields=["status", "match"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "match"],
                condition=Q(status="pending"),  # solo uno pendiente por (user, match)
                name="uniq_pending_payment_per_user_match",
            ),
        ]

    def __str__(self):
        return f"{self.public_id} | {self.user_id} | {self.match_id} | {self.status}"
