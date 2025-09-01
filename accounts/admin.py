from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.api.models import User, SessionToken


class SessionTokenInline(admin.TabularInline):
    model = SessionToken
    fields = ("device_id", "short_token", "ip_address", "user_agent", "created_at", "last_seen")
    readonly_fields = ("device_id", "short_token", "ip_address", "user_agent", "created_at", "last_seen")
    extra = 0
    can_delete = True

    def short_token(self, obj):
        return (obj.token[:16] + "…") if obj.token else "-"

    short_token.short_description = "token"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("username", "email", "document_type", "document_number", "is_active", "is_staff")
    ordering = ("username",)
    search_fields = ("username", "email", "document_number", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Identidad", {"fields": ("first_name", "last_name", "phone", "date_of_birth", "marketing_opt_in",
                                  "document_type", "document_number")}),
        ("Dirección", {"fields": ("address", "reference", "district", "city", "region", "country", "postal_code")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active")}),
    )
    inlines = [SessionTokenInline]


@admin.register(SessionToken)
class SessionTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "device_id", "short_token", "ip_address", "created_at", "last_seen")
    search_fields = ("user__username", "user__email", "user__document_number", "device_id", "token")
    list_filter = ("device_id",)
    ordering = ("-created_at",)

    def short_token(self, obj):
        return (obj.token[:24] + "…") if obj.token else "-"

    short_token.short_description = "token"
