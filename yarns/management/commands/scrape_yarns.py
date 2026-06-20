import requests
from django.core.management.base import BaseCommand

from color.selector import ColorSelector
from scrapers import SCRAPERS
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Scrape yarn data from one or all sources and upsert into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SCRAPERS.keys()),
            default=None,
            help="Only scrape this source (default: all)",
        )

    def handle(self, *args, **options):
        selector = ColorSelector()
        sources = [options["source"]] if options["source"] else list(SCRAPERS.keys())

        for source_id in sources:
            self.stdout.write(f"Scraping {source_id}...")
            scraper = SCRAPERS[source_id]()
            yarn_data = scraper.scrape()

            created = updated = 0
            for data in yarn_data:
                color = None
                try:
                    response = requests.get(data["image_url"], timeout=10)
                    color = selector.get_color_from_bytes(response.content)
                except Exception as e:
                    self.stdout.write(f"  Color fetch failed for {data['name']}: {e}")

                _, is_new = Yarn.objects.update_or_create(
                    url=data["url"],
                    defaults={
                        "name": data["name"],
                        "image_url": data["image_url"],
                        "source": source_id,
                        "color_r": color[0] if color else None,
                        "color_g": color[1] if color else None,
                        "color_b": color[2] if color else None,
                    },
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(
                self.style.SUCCESS(f"  Done: {created} created, {updated} updated")
            )
