"""Import map specifiers owned by vor_archives.

Combines shared vor_archives JS (common, events, shared/pure) with
per-page submodule importmaps (artworks, attributes, dashboard). Same
shape as vor_archives/urls.py including artworks.urls and the other
per-page urlconf, if any.
"""

from config.importmap import build_importmap

_SHARED_IMPORTMAP_PATHS = {
    "@vor/common": "vor_archives/js/common.js",
    "@vor/events/list": "vor_archives/js/events/list.js",
    "@vor/shared/pure/cookies": "vor_archives/js/shared/pure/cookies.js",
    "@vor/shared/pure/urls": "vor_archives/js/shared/pure/urls.js",
    "@vor/shared/pure/wheel": "vor_archives/js/shared/pure/wheel.js",
    "@vor/shared/csrf": "vor_archives/js/shared/csrf.js",
    "@vor/shared/cover": "vor_archives/js/shared/cover.js",
    "@vor/shared/dom": "vor_archives/js/shared/dom.js",
}

_PAGE_IMPORTMAP_MODULES = [
    "apps.vor_archives.artworks.importmap",
    "apps.vor_archives.attributes_importmap",
    "apps.vor_archives.dashboard_importmap",
]

IMPORTMAP_PATHS = build_importmap(
    _SHARED_IMPORTMAP_PATHS,
    *_PAGE_IMPORTMAP_MODULES,
)
