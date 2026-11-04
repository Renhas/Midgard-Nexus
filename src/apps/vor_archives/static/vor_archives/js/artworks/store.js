/* ============================================
   Composition: filters + collections + drag + menu + search + delete
   ============================================ */
import { getAlpine } from "@lib/alpine";
import { filtersMixin } from "./store/filters.js";
import { collectionsMixin } from "./store/collections.js";
import { dragMixin } from "./store/drag.js";
import { menuMixin } from "./store/menu.js";
import { searchMixin } from "./store/search.js";
import { deleteMixin } from "./store/delete.js";

document.addEventListener("alpine:init", () => {
  getAlpine().store("vorArtworks", {
    isStaff: false,
    _booted: false,

    ...filtersMixin,
    ...collectionsMixin,
    ...dragMixin,
    ...menuMixin,
    ...searchMixin,
    ...deleteMixin,

    initFromPage(opts) {
      if (this._booted) return;
      this._booted = true;

      // filters
      this.listUrl = opts.listUrl || "";
      this.filterCatalog = { ...this.filterCatalog, ...(opts.filterCatalog || {}) };

      // collections
      this.collectionBaseUrl = opts.collectionBaseUrl || "";
      this.collectionTreeUrl = opts.collectionTreeUrl || "";
      this.collectionReorderUrl = opts.collectionReorderUrl || "";

      // drag
      this.reorderUrl = opts.reorderUrl || "";

      // search
      this.searchUrl = opts.searchUrl || "";
      this.attachUrl = opts.attachUrl || "";

      // base
      this.isStaff = Boolean(opts.isStaff);

      // bootstrap (порядок важен: сначала данные, потом рендер)
      this.resetFilters(false);
      this.restoreSidebar();
      this.persistSidebar();
      this.applyListState();
      this.reloadList();
      this.syncCollectionSortable();
      this.applyCollectionTreeState();
    },
  });
});
