from django.core import serializers
from yarns.models import Yarn

qs = Yarn.objects.filter(source__in=["lovecrafts", "icewear"])

with open("lovecrafts_icewear.json", "w") as f:
    serializers.serialize("json", qs, stream=f, indent=2)