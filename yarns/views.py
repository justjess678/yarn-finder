from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from color.selector import ColorSelector, color_difference
from scrapers import SCRAPERS
from .models import Yarn, YarnType, Favourite

ITEMS_PER_PAGE = 9
MAX_RESULTS = 200
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
    brands = post.getlist("brands")
    if brands and set(brands) != set(_all_source_ids()):
        filters["brands"] = brands
    return filters


def _apply_filters(queryset, filters):
    if f := filters.get("fiber"):
        queryset = queryset.filter(fiber__icontains=f)
    if t := filters.get("yarn_type"):
        queryset = queryset.filter(yarn_type=t)
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
    source_names = {cls.source_id: cls.display_name for cls in SCRAPERS.values()}
    results = sorted(
        [
            {
                "yarn": yarn,
                "score": color_difference(reference_color, yarn.dominant_color),
                "source_name": source_names.get(yarn.source, yarn.source),
            }
            for yarn in yarns
        ],
        key=lambda x: x["score"],
    )[:MAX_RESULTS]

    paginator = Paginator(results, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(
            Favourite.objects.filter(user=request.user).values_list("yarn_id", flat=True)
        )

    return render(request, "yarns/results.html", {
        "page_obj": page_obj,
        "total_count": len(results),
        "reference_color": "rgb({},{},{})".format(*reference_color),
        "filters": filters,
        "fav_ids": fav_ids,
    })


@login_required
@require_POST
def toggle_favourite(request, yarn_id):
    yarn = get_object_or_404(Yarn, pk=yarn_id)
    fav, created = Favourite.objects.get_or_create(user=request.user, yarn=yarn)
    if not created:
        fav.delete()
    return JsonResponse({"starred": created})


@login_required
def profile(request):
    favourites = (
        Favourite.objects.filter(user=request.user)
        .select_related("yarn")
        .order_by("yarn__name")
    )
    return render(request, "yarns/profile.html", {"favourites": favourites})
