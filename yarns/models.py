from django.contrib.auth.models import User
from django.db import models


class YarnType(models.TextChoices):
    LACE       = "lace",        "Lace"
    FINGERING  = "fingering",   "Fingering"
    SPORT      = "sport",       "Sport"
    DK         = "dk",          "DK"
    WORSTED    = "worsted",     "Worsted"
    ARAN       = "aran",        "Aran"
    BULKY      = "bulky",       "Bulky"
    SUPER_BULKY = "super_bulky", "Super Bulky"
    JUMBO      = "jumbo",       "Jumbo"


class Yarn(models.Model):
    name = models.CharField(max_length=1000)
    url = models.URLField(unique=True)
    image_url = models.URLField()
    source = models.CharField(max_length=50)
    color_r = models.PositiveSmallIntegerField(null=True)
    color_g = models.PositiveSmallIntegerField(null=True)
    color_b = models.PositiveSmallIntegerField(null=True)
    fiber = models.CharField(max_length=255, blank=True, default="")
    yarn_type = models.CharField(max_length=100, blank=True, default="")
    last_scraped = models.DateTimeField(auto_now=True)

    @property
    def dominant_color(self):
        if self.color_r is not None:
            return (self.color_r, self.color_g, self.color_b)
        return None

    def __str__(self):
        return f"{self.name} ({self.source})"

    class Meta:
        ordering = ["source", "name"]


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favourites")
    yarn = models.ForeignKey(Yarn, on_delete=models.CASCADE, related_name="favourited_by")

    class Meta:
        unique_together = ("user", "yarn")
