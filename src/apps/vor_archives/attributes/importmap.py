"""Import map specifiers owned by the attributes page."""

from config.importmap import build_importmap

_OWN_IMPORTMAP_PATHS = {
    "@vor/attributes/attributes": "vor_archives/js/attributes/attributes.js",
    "@vor/attributes/pure/selection": "vor_archives/js/attributes/pure/selection.js",
    "@vor/events/attributes": "vor_archives/js/events/attributes.js",
}

_SUBMODULE_IMPORTMAP_MODULES: list[str] = []

IMPORTMAP_PATHS = build_importmap(
    _OWN_IMPORTMAP_PATHS,
    *_SUBMODULE_IMPORTMAP_MODULES,
)
