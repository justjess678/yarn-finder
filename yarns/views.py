from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from color.selector import ColorSelector, color_difference
from scrapers import SCRAPERS
from .models import Yarn, YarnType

ITEMS_PER_PAGE = 9
_selector = ColorSelector()


def index(request):
    sources = [cls for cls in SCRAPERS.values() if cls.display_name]
    return render(request, "yarns/index.html", {
        "yarn_count": Yarn.objects.count(),
        "sources": sources,
        "yarn_types": YarnType.choices,
    })


def _hex_to_rgb(hex_color: str) -> tuple | None:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return None
    try:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    except ValueError:
        return None


def _all_source_ids():
    return list(SCRAPERS.keys())


def _parse_filters(post):
    filters = {}
    if fiber := post.get("fiber", "").strip():
        filters["fiber"] = fiber
    if yarn_type := post.get("yarn_type", "").strip():
        filters["yarn_type"] = yarn_type
    if (v := post.get("min_weight", "").strip()).isdigit():
        filters["min_weight"] = int(v)
    if (v := post.get("max_weight", "").strip()).isdigit():
        filters["max_weight"] = int(v)
    brands = post.getlist("brands")
    if brands and set(brands) != set(_all_source_ids()):
        filters["brands"] = brands
    return filters


def _apply_filters(queryset, filters):
    if f := filters.get("fiber"):
        queryset = queryset.filter(fiber__icontains=f)
    if t := filters.get("yarn_type"):
        queryset = queryset.filter(yarn_type=t)
    if w := filters.get("min_weight"):
        queryset = queryset.filter(skein_weight_grams__gte=w)
    if w := filters.get("max_weight"):
        queryset = queryset.filter(skein_weight_grams__lte=w)
    if brands := filters.get("brands"):
        queryset = queryset.filter(source__in=brands)
    return queryset


def search(request):
    if request.method == "POST":
        ref_file = request.FILES.get("reference_image")
        color_hex = request.POST.get("color_hex", "").strip()

        if ref_file:
            reference_color = _selector.get_color_from_bytes(ref_file.read())
        elif color_hex:
            reference_color = _hex_to_rgb(color_hex)
        else:
            return redirect("index")

        if not reference_color:
            return render(request, "yarns/index.html", {
                "error": "No dominant color found — the image may be entirely white.",
                "yarn_count": Yarn.objects.count(),
                "yarn_types": YarnType.choices,
                "sources": [cls for cls in SCRAPERS.values() if cls.display_name],
            })

        request.session["reference_color"] = list(reference_color)
        request.session["filters"] = _parse_filters(request.POST)
    else:
        stored = request.session.get("reference_color")
        if not stored:
            return redirect("index")
        reference_color = tuple(stored)

    filters = request.session.get("filters", {})
    yarns = _apply_filters(Yarn.objects.exclude(color_r=None), filters)
    results = sorted(
        [
            {"yarn": yarn, "score": color_difference(reference_color, yarn.dominant_color)}
            for yarn in yarns
        ],
        key=lambda x: x["score"],
    )

    paginator = Paginator(results, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "yarns/results.html", {
        "page_obj": page_obj,
        "total_count": len(results),
        "reference_color": "rgb({},{},{})".format(*reference_color),
        "filters": filters,
    })
