# admin.py
from django.contrib import admin

from matches.api.models import Team, Location, Match, MatchFAQ, MatchRecommendation, Enrollment


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("field_name", "district", "address", "is_active")
    list_filter = ("is_active", "district__city")
    search_fields = ("field_name", "address", "district__name")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "start_at", "capacity", "status")
    list_filter = ("status", "location__district")
    search_fields = ("title", "location__field_name")
    autocomplete_fields = ("location",)


@admin.register(MatchFAQ)
class MatchFAQAdmin(admin.ModelAdmin):
    list_display = ("match", "question")


@admin.register(MatchRecommendation)
class MatchRecommendationAdmin(admin.ModelAdmin):
    list_display = ("match", "text")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("match", "user", "is_active", "joined_at", "cancelled_at")
    list_filter = ("is_active", "match__status")
    search_fields = ("match__title", "user__email")
