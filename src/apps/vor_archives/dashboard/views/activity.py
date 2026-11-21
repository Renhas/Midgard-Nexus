from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..forms import FeedPaginationForm, HeatmapFilterForm
from ..services import feed_context, heatmap_payload


@login_required
@require_GET
def dashboard_feed(request):
    offset = FeedPaginationForm(request.GET).get_offset()
    return render(
        request,
        "vor_archives/partials/dashboard/dash_feed_items.html",
        feed_context(request.user, offset=offset),
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
