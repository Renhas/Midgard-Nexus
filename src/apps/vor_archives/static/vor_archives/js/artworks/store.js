/* ============================================
   Composition: filters + collections + drag + menu + search + delete
   ============================================ */
import { getAlpine } from "@lib/alpine";
import { filtersMixin } from "@vor/artworks/store/filters";
import { collectionsMixin } from "@vor/artworks/store/collections";
import { dragMixin } from "@vor/artworks/store/drag";
import { menuMixin } from "@vor/artworks/store/menu";
import { searchMixin } from "@vor/artworks/store/search";
import { deleteMixin } from "@vor/artworks/store/delete";

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
