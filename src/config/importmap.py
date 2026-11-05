"""Global import map assembled from per-app registries.

Mirrors config/urls.py: the central file lists which apps contribute
specifiers, each app owns its own mapping in <app>/importmap.py and may
in turn include its own submodules. Vendor wrappers are global
(src/static/js/lib/, served from STATICFILES_DIRS) and are listed here
directly.

Usage from an app's importmap.py:

    from config.importmap import build_importmap

    _OWN_PATHS = {"@vor/common": "vor_archives/js/common.js"}
    _SUBMODULE_IMPORTMAP_MODULES = ["apps.vor_archives.artworks.importmap"]

    IMPORTMAP_PATHS = build_importmap(_OWN_PATHS, *_SUBMODULE_IMPORTMAP_MODULES)
"""

from importlib import import_module
from typing import Any


def build_importmap(*sources: dict[str, str] | str) -> dict[str, str]:
    """Merge import map specifiers from dicts and dotted module paths.

    Each source is either a {specifier: path} dict or a dotted module
    path whose module exposes IMPORTMAP_PATHS (same shape). Later sources
    override earlier ones; duplicate specifiers across sources raise an
    error so typos surface at startup, not at runtime in the browser.
    """
    paths: dict[str, str] = {}
    for source in sources:
        if isinstance(source, dict):
            mapping = source
        else:
            module: Any = import_module(source)
            mapping = module.IMPORTMAP_PATHS
        overlap = paths.keys() & mapping.keys()
        if overlap:
            raise RuntimeError(
                f"Duplicate import map specifiers from {source!r}: {sorted(overlap)}"
            )
        paths.update(mapping)
    return paths


VENDOR_IMPORTMAP_PATHS = {
    "@lib/htmx": "js/lib/htmx.js",
    "@lib/alpine": "js/lib/alpine.js",
    "@lib/sortable": "js/lib/sortable.js",
    "@lib/chart": "js/lib/chart.js",
}

APP_IMPORTMAP_MODULES = [
    "apps.vor_archives.importmap",
    # future: "apps.fafnir_cave.importmap",
    # future: "apps.kvasir_records.importmap",
]

IMPORTMAP_PATHS = build_importmap(
    VENDOR_IMPORTMAP_PATHS,
    *APP_IMPORTMAP_MODULES,
)
