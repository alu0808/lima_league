from django.contrib import admin
from matches.api.models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)