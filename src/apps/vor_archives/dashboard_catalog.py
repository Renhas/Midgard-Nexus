DASHBOARD_TABS = [
    {"kind": "stats", "label": "Статистика", "icon": "bi bi-123"},
    {"kind": "charts", "label": "Графики", "icon": "bi bi-pie-chart"},
    {"kind": "activity", "label": "Активность", "icon": "bi bi-calendar-date"},
]

DEFAULT_DASH_TAB = "stats"

DASH_TAB_KINDS = {tab["kind"] for tab in DASHBOARD_TABS}


def get_dash_tab(kind):
    for tab in DASHBOARD_TABS:
        if tab["kind"] == kind:
            return tab
    return None
