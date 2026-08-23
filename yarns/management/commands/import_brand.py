import json
from django.core.management.base import BaseCommand

from scrapers import SCRAPERS
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Import yarn data from JSON file, replacing existing entries for that brand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SCRAPERS.keys()),
            required=True,
            help="Source brand",
        )
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Input JSON file",
        )

    def handle(self, *args, **options):
        source = options["source"]
        input_file = options["file"]

        # Load JSON data
        try:
            with open(input_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {input_file}"))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in {input_file}"))
            return

        # Delete existing entries for this source
        old_count = Yarn.objects.filter(source=source).count()
        if old_count:
            self.stdout.write(f"Deleting {old_count} existing entries for '{source}'...")
            Yarn.objects.filter(source=source).delete()

        # Import new entries
        created = 0
        for yarn_data in data:
            Yarn.objects.create(
                name=yarn_data["name"],
                url=yarn_data["url"],
                image_url=yarn_data["image_url"],
                source=yarn_data["source"],
                color_r=yarn_data.get("color_r"),
                color_g=yarn_data.get("color_g"),
                color_b=yarn_data.get("color_b"),
                fiber=yarn_data.get("fiber", ""),
                yarn_type=yarn_data.get("yarn_type", ""),
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} yarns from '{source}'"
            )
        )
