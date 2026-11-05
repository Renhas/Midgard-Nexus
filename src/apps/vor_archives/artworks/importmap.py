"""Import map specifiers owned by the artworks page."""

from config.importmap import build_importmap

_OWN_IMPORTMAP_PATHS = {
    "@vor/artworks/api": "vor_archives/js/artworks/api.js",
    "@vor/artworks/helpers": "vor_archives/js/artworks/helpers.js",
    "@vor/artworks/store": "vor_archives/js/artworks/store.js",
    "@vor/artworks/store/filters": "vor_archives/js/artworks/store/filters.js",
    "@vor/artworks/store/collections": "vor_archives/js/artworks/store/collections.js",
    "@vor/artworks/store/drag": "vor_archives/js/artworks/store/drag.js",
    "@vor/artworks/store/menu": "vor_archives/js/artworks/store/menu.js",
    "@vor/artworks/store/search": "vor_archives/js/artworks/store/search.js",
    "@vor/artworks/store/delete": "vor_archives/js/artworks/store/delete.js",
    "@vor/artworks/overlay": "vor_archives/js/artworks/overlay.js",
    "@vor/artworks/add": "vor_archives/js/artworks/add.js",
    "@vor/artworks/chip": "vor_archives/js/artworks/chip.js",
    "@vor/artworks/row_preview": "vor_archives/js/artworks/row_preview.js",
}

# When artworks gets its own nested importmap modules (e.g. store/),
# list them here instead of expanding _OWN_IMPORTMAP_PATHS.
_SUBMODULE_IMPORTMAP_MODULES: list[str] = []

IMPORTMAP_PATHS = build_importmap(
    _OWN_IMPORTMAP_PATHS,
    *_SUBMODULE_IMPORTMAP_MODULES,
)
