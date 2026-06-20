from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from color.selector import ColorSelector, color_difference
from .models import Yarn

ITEMS_PER_PAGE = 9
_selector = ColorSelector()


def index(request):
    return render(request, "yarns/index.html", {
        "yarn_count": Yarn.objects.count(),
    })


def search(request):
    if request.method == "POST":
        ref_file = request.FILES.get("reference_image")
        if not ref_file:
            return redirect("index")

        reference_color = _selector.get_color_from_bytes(ref_file.read())
        if not reference_color:
            return render(request, "yarns/index.html", {
                "error": "No dominant color found — the image may be entirely white.",
                "yarn_count": Yarn.objects.count(),
            })

        request.session["reference_color"] = list(reference_color)
    else:
        stored = request.session.get("reference_color")
        if not stored:
            return redirect("index")
        reference_color = tuple(stored)

    yarns = Yarn.objects.exclude(color_r=None)
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
    })
