from django.contrib import admin

from .models import PlayerMatchStat


@admin.register(PlayerMatchStat)
class PlayerMatchStatAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "match", "goals", "is_winner", "is_mvp", "created_at")
    list_editable = ("goals", "is_winner", "is_mvp")
    search_fields = ("user__email", "user__first_name", "user__last_name", "match__title")
    list_filter = ("is_winner", "is_mvp")
