import json
from django.core.management.base import BaseCommand

from scrapers import SCRAPERS
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Export yarn data for a brand to JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SCRAPERS.keys()),
            required=True,
            help="Source to export",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Output file (default: <source>.json)",
        )

    def handle(self, *args, **options):
        source = options["source"]
        output_file = options["output"] or f"{source}.json"

        yarns = Yarn.objects.filter(source=source).values(
            "name", "url", "image_url", "source", "color_r", "color_g", "color_b",
            "fiber", "yarn_type"
        )

        data = list(yarns)
        count = len(data)

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f"Exported {count} yarns from '{source}' to {output_file}")
        )
