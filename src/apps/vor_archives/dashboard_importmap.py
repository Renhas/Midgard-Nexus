"""Import map specifiers owned by the dashboard page."""

from config.importmap import build_importmap

_OWN_IMPORTMAP_PATHS = {
    "@vor/dashboard/charts": "vor_archives/js/dashboard/charts.js",
    "@vor/dashboard/dashboard": "vor_archives/js/dashboard/dashboard.js",
}

_SUBMODULE_IMPORTMAP_MODULES: list[str] = []

IMPORTMAP_PATHS = build_importmap(
    _OWN_IMPORTMAP_PATHS,
    *_SUBMODULE_IMPORTMAP_MODULES,
)
