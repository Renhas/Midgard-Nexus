"""Import map specifiers owned by the dashboard page."""

from config.importmap import build_importmap

_OWN_IMPORTMAP_PATHS = {
    "@vor/dashboard/attrs": "vor_archives/js/dashboard/attrs.js",
    "@vor/dashboard/charts": "vor_archives/js/dashboard/charts.js",
    "@vor/dashboard/dashboard": "vor_archives/js/dashboard/dashboard.js",
    "@vor/dashboard/pure/metrics": "vor_archives/js/dashboard/pure/metrics.js",
    "@vor/dashboard/stats": "vor_archives/js/dashboard/stats.js",
}

_SUBMODULE_IMPORTMAP_MODULES: list[str] = []

IMPORTMAP_PATHS = build_importmap(
    _OWN_IMPORTMAP_PATHS,
    *_SUBMODULE_IMPORTMAP_MODULES,
)
