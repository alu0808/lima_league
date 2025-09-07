from django.contrib import admin

from .models import Banner, Sponsor


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "description", "path")
    list_filter = ("is_active",)
    ordering = ("order", "id")


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title",)
    list_filter = ("is_active",)
    ordering = ("order", "id")
