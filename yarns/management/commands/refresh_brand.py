from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from scrapers import SCRAPERS
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Delete and re-scrape a yarn brand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SCRAPERS.keys()),
            required=True,
            help="Source to refresh",
        )

    def handle(self, *args, **options):
        source = options["source"]

        # Delete existing entries
        count = Yarn.objects.filter(source=source).count()
        if count:
            self.stdout.write(f"Deleting {count} existing entries for '{source}'...")
            Yarn.objects.filter(source=source).delete()

        # Re-scrape
        self.stdout.write(f"Scraping '{source}'...")
        try:
            call_command("scrape_yarns", source=source)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully refreshed '{source}'")
            )
        except Exception as e:
            raise CommandError(f"Scraping failed: {e}")
