from django.http import Http404
from django.shortcuts import render

from apps.vor_archives.utils import module_base_context

from ..catalog import DASHBOARD_TABS, DashboardTab, get_dash_tab


def dash_tab_or_404(tab_kind: str) -> DashboardTab:
    tab = get_dash_tab(tab_kind)
    if tab is None:
        raise Http404("Неизвестная вкладка дашборда")
    return tab


def render_dashboard_shell(
    request,
    tab: DashboardTab | str,
    extra: dict | None = None,
):
    resolved_tab = dash_tab_or_404(tab) if isinstance(tab, str) else tab
    context = {
        **module_base_context("dashboard", hide_right=True),
        "dash_kind": resolved_tab["kind"],
        "dash_tabs": DASHBOARD_TABS,
        "dash_tab": resolved_tab,
    }
    if extra:
        context.update(extra)
    return render(request, "vor_archives/dashboard.html", context)
