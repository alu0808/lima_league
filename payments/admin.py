from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "public_id", "user", "match", "amount", "currency",
        "status", "mp_status", "created_at",
    )
    search_fields = ("public_id", "mp_payment_id", "external_reference", "user__email")
    list_filter = ("status", "mp_status", "currency")
    readonly_fields = (
        "public_id", "preference_id", "init_point", "sandbox_init_point",
        "mp_payment_id", "mp_status", "external_reference", "created_at", "updated_at",
    )
