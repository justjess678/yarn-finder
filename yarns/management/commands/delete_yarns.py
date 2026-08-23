from django.core.management.base import BaseCommand

from scrapers import SCRAPERS
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Delete yarn entries by source"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SCRAPERS.keys()),
            required=True,
            help="Source to delete entries from",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        source = options["source"]
        count = Yarn.objects.filter(source=source).count()

        if not count:
            self.stdout.write(f"No yarns found for source '{source}'")
            return

        if not options["confirm"]:
            confirm = input(
                f"Delete {count} yarns from '{source}'? (yes/no): "
            )
            if confirm.lower() != "yes":
                self.stdout.write("Cancelled.")
                return

        deleted_count, _ = Yarn.objects.filter(source=source).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} yarns from '{source}'")
        )
