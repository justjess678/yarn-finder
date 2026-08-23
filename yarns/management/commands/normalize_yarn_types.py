from django.core.management.base import BaseCommand

from color.yarn_utils import normalize_yarn_type
from yarns.models import Yarn


class Command(BaseCommand):
    help = "Normalize existing yarn type values to standard categories"

    def handle(self, *args, **options):
        updated = 0
        for yarn in Yarn.objects.exclude(yarn_type=""):
            normalized = normalize_yarn_type(yarn.yarn_type)
            if normalized and normalized != yarn.yarn_type:
                yarn.yarn_type = normalized
                yarn.save(update_fields=["yarn_type"])
                updated += 1
                self.stdout.write(f"  {yarn.name}: {yarn.yarn_type}")

        self.stdout.write(self.style.SUCCESS(f"Normalized {updated} yarn types"))
