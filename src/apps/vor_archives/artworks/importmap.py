"""Import map specifiers owned by the artworks page."""

from config.importmap import build_importmap

_PAGE_PATHS = {
    "@vor/artworks/add": "vor_archives/js/artworks/add.js",
    "@vor/artworks/api": "vor_archives/js/artworks/api.js",
    "@vor/artworks/chip": "vor_archives/js/artworks/chip.js",
    "@vor/artworks/overlay": "vor_archives/js/artworks/overlay.js",
    "@vor/artworks/overlay_mixins": "vor_archives/js/artworks/overlay_mixins.js",
    "@vor/artworks/row_preview": "vor_archives/js/artworks/row_preview.js",
    "@vor/artworks/store": "vor_archives/js/artworks/store.js",
    "@vor/artworks/store/collections": "vor_archives/js/artworks/store/collections.js",
    "@vor/artworks/store/delete": "vor_archives/js/artworks/store/delete.js",
    "@vor/artworks/store/drag": "vor_archives/js/artworks/store/drag.js",
    "@vor/artworks/store/filters": "vor_archives/js/artworks/store/filters.js",
    "@vor/artworks/store/menu": "vor_archives/js/artworks/store/menu.js",
    "@vor/artworks/store/search": "vor_archives/js/artworks/store/search.js",
}

_MIXIN_PATHS = {
    "@vor/artworks/mixins/age_picker": "vor_archives/js/artworks/mixins/age_picker.js",
    "@vor/artworks/mixins/attach": "vor_archives/js/artworks/mixins/attach.js",
    "@vor/artworks/mixins/attributes": "vor_archives/js/artworks/mixins/attributes.js",
    "@vor/artworks/mixins/cover": "vor_archives/js/artworks/mixins/cover.js",
    "@vor/artworks/mixins/datepicker": "vor_archives/js/artworks/mixins/datepicker.js",
    "@vor/artworks/mixins/number_wheel": "vor_archives/js/artworks/mixins/number_wheel.js",
    "@vor/artworks/mixins/overlay_lifecycle": "vor_archives/js/artworks/mixins/overlay_lifecycle.js",
    "@vor/artworks/mixins/progress": "vor_archives/js/artworks/mixins/progress.js",
    "@vor/artworks/mixins/rating": "vor_archives/js/artworks/mixins/rating.js",
    "@vor/artworks/mixins/relations": "vor_archives/js/artworks/mixins/relations.js",
    "@vor/artworks/mixins/status": "vor_archives/js/artworks/mixins/status.js",
    "@vor/artworks/mixins/work_fields": "vor_archives/js/artworks/mixins/work_fields.js",
}

_PURE_PATHS = {
    "@vor/artworks/pure/catalogs": "vor_archives/js/artworks/pure/catalogs.js",
    "@vor/artworks/pure/chip_fit": "vor_archives/js/artworks/pure/chip_fit.js",
    "@vor/artworks/pure/collection_tree": "vor_archives/js/artworks/pure/collection_tree.js",
    "@vor/artworks/pure/collection_urls": "vor_archives/js/artworks/pure/collection_urls.js",
    "@vor/artworks/pure/dates": "vor_archives/js/artworks/pure/dates.js",
    "@vor/artworks/pure/draft": "vor_archives/js/artworks/pure/draft.js",
    "@vor/artworks/pure/filter_selection": "vor_archives/js/artworks/pure/filter_selection.js",
    "@vor/artworks/pure/form_state": "vor_archives/js/artworks/pure/form_state.js",
    "@vor/artworks/pure/popover": "vor_archives/js/artworks/pure/popover.js",
    "@vor/artworks/pure/progress": "vor_archives/js/artworks/pure/progress.js",
    "@vor/artworks/pure/quick_state": "vor_archives/js/artworks/pure/quick_state.js",
    "@vor/artworks/pure/rating": "vor_archives/js/artworks/pure/rating.js",
    "@vor/artworks/pure/relations": "vor_archives/js/artworks/pure/relations.js",
}

# When artworks gets its own nested importmap modules (e.g. store/),
# list them here instead of expanding the dicts above.
_SUBMODULE_IMPORTMAP_MODULES: list[str] = []

IMPORTMAP_PATHS = build_importmap(
    _PAGE_PATHS,
    _MIXIN_PATHS,
    _PURE_PATHS,
    *_SUBMODULE_IMPORTMAP_MODULES,
)
