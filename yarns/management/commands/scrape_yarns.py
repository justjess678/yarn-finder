import gc

from django.core.management.base import BaseCommand

from color.selector import ColorSelector
from color.yarn_utils import normalize_yarn_type
from scrapers import SCRAPERS
from yarns.models import Yarn

GC_INTERVAL = 50


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
            try:
                scraper = SCRAPERS[source_id]()
                yarn_data = scraper.scrape()

                count = 0
                existing_colors = {
                    yarn.url: (yarn.color_r, yarn.color_g, yarn.color_b)
                    for yarn in Yarn.objects.filter(source=source_id, color_r__isnull=False)
                }

                for data in yarn_data:
                    cached = existing_colors.get(data["url"])
                    if cached:
                        color = cached
                    else:
                        color = None
                        try:
                            color = selector.get_color_from_url(data["image_url"])
                        except Exception as e:
                            self.stdout.write(f"  Color fetch failed for {data['name']}: {e}")

                    Yarn.objects.update_or_create(
                        url=data["url"],
                        defaults={
                            "name": data["name"],
                            "image_url": data["image_url"],
                            "source": source_id,
                            "color_r": color[0] if color else None,
                            "color_g": color[1] if color else None,
                            "color_b": color[2] if color else None,
                            "fiber": data.get("fiber", ""),
                            "yarn_type": normalize_yarn_type(data.get("yarn_type", "")),
                        },
                    )
                    count += 1
                    if count % GC_INTERVAL == 0:
                        gc.collect()

                self.stdout.write(self.style.SUCCESS(f"  Done: {count} yarns processed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Source {source_id} failed: {e}"))
