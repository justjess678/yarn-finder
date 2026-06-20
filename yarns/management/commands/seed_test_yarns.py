from django.core.management.base import BaseCommand
from yarns.models import Yarn

TEST_YARNS = [
    # (name, r, g, b)
    ("Mega Wool - Cherry Red",        180,  30,  30),
    ("Mega Wool - Coral",             220,  90,  70),
    ("Mega Wool - Dusty Rose",        200, 130, 130),
    ("Mega Wool - Hot Pink",          210,  50, 120),
    ("Mega Wool - Tangerine",         230, 120,  30),
    ("Mega Wool - Mustard",           200, 165,  40),
    ("Mega Wool - Lemon Yellow",      230, 220,  60),
    ("Mega Wool - Olive",             100, 120,  50),
    ("Mega Wool - Grass Green",        60, 150,  60),
    ("Mega Wool - Sage",              130, 160, 120),
    ("Mega Wool - Teal",               30, 140, 130),
    ("Mega Wool - Sky Blue",           80, 160, 210),
    ("Mega Wool - Royal Blue",         30,  70, 180),
    ("Mega Wool - Navy",               20,  30,  90),
    ("Mega Wool - Lavender",          170, 140, 210),
    ("Mega Wool - Purple",            110,  40, 160),
    ("Mega Wool - Burgundy",          120,  20,  50),
    ("Mega Wool - Chocolate Brown",    90,  50,  20),
    ("Mega Wool - Camel",             190, 150,  90),
    ("Mega Wool - Stone Grey",        130, 130, 130),
    ("Mega Wool - Charcoal",           60,  60,  60),
    ("Mega Wool - Cream",             230, 220, 200),
]

SOURCE = "ice_yarns"
BASE_URL = "https://www.iceyarns.com/test-yarn-{}"


def _hex(r, g, b):
    return f"{r:02x}{g:02x}{b:02x}"


class Command(BaseCommand):
    help = "Seed the database with test yarn data for development"

    def handle(self, *args, **options):
        created = updated = 0
        for i, (name, r, g, b) in enumerate(TEST_YARNS):
            hex_color = _hex(r, g, b)
            image_url = f"https://placehold.co/200x200/{hex_color}/ffffff.jpg"

            _, is_new = Yarn.objects.update_or_create(
                url=BASE_URL.format(i),
                defaults={
                    "name": name,
                    "image_url": image_url,
                    "source": SOURCE,
                    "color_r": r,
                    "color_g": g,
                    "color_b": b,
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done: {created} created, {updated} updated")
        )
