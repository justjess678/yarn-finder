from django.contrib import admin
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import path

from .models import Yarn


@admin.register(Yarn)
class YarnAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "has_color", "last_scraped")
    list_filter = ("source",)
    search_fields = ("name",)
    readonly_fields = ("last_scraped",)
    actions = ["rescrape_sources"]

    @admin.display(boolean=True, description="Color indexed")
    def has_color(self, obj):
        return obj.color_r is not None

    @admin.action(description="Re-scrape sources for selected yarns")
    def rescrape_sources(self, request, queryset):
        sources = set(queryset.values_list("source", flat=True))
        for source in sources:
            call_command("scrape_yarns", source=source)
        self.message_user(request, f"Scraped: {', '.join(sources)}")

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "scrape-all/",
                self.admin_site.admin_view(self._scrape_all_view),
                name="yarns_scrape_all",
            ),
        ] + urls

    def _scrape_all_view(self, request):
        call_command("scrape_yarns")
        self.message_user(request, "All sources scraped.")
        return HttpResponseRedirect("../")
