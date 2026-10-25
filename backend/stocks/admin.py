from django.contrib import admin

from stocks.models import EconomicEvent


@admin.register(EconomicEvent)
class EconomicEventAdmin(admin.ModelAdmin):
    list_display = ("event_date", "country", "importance", "title")
    list_filter = ("country", "importance", "event_date")
    search_fields = ("title",)
