from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..forms import FeedPaginationForm, HeatmapFilterForm
from ..services import feed_page, heatmap_payload


@login_required
@require_GET
def dashboard_feed(request):
    offset = FeedPaginationForm(request.GET).get_offset()
    items, has_more = feed_page(request.user, offset=offset)
    return render(
        request,
        "vor_archives/partials/dashboard/dash_feed_items.html",
        {
            "feed_items": items,
            "feed_has_more": has_more,
            "feed_next_offset": offset + len(items),
        },
    )


@login_required
@require_GET
def dashboard_heatmap(request):
    year = HeatmapFilterForm(request.GET).get_year()
    return render(
        request,
        "vor_archives/partials/dashboard/dash_heatmap.html",
        {"heatmap": heatmap_payload(request.user, year=year)},
    )
