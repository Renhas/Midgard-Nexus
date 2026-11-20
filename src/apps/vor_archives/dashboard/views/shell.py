from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..catalog import DEFAULT_DASH_TAB
from ..forms import HeatmapFilterForm
from ..services import (
    attrs_payload,
    feed_page,
    heatmap_payload,
    stats_payload,
)
from .utils import dash_tab_or_404, render_dashboard_shell


@login_required
def dashboard(request):
    """Страница дашборда — редирект на вкладку статистики."""
    return redirect("vor_archives:dashboard:tab", tab=DEFAULT_DASH_TAB)


@login_required
def dashboard_tab(request, tab):
    """Оболочка дашборда для выбранной вкладки."""
    dash_tab_or_404(tab)
    extra = {}
    if tab == "stats":
        extra.update(stats_payload(request.user))
    elif tab == "attrs":
        extra.update(attrs_payload(request.user))
    elif tab == "activity":
        year = HeatmapFilterForm(request.GET).get_year()
        items, has_more = feed_page(request.user)
        extra.update(
            {
                "feed_items": items,
                "feed_has_more": has_more,
                "feed_next_offset": len(items),
                "heatmap": heatmap_payload(request.user, year=year),
            }
        )
    return render_dashboard_shell(request, tab, extra)
