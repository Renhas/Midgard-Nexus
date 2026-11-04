(function () {
  /* ============================================
     Composition: filters + collections + drag + menu + search + delete
     ============================================ */
  document.addEventListener("alpine:init", () => {
    Alpine.store("vorArtworks", {
      isStaff: false,
      _booted: false,

      ...window.VorMixin.filters,
      ...window.VorMixin.collections,
      ...window.VorMixin.drag,
      ...window.VorMixin.menu,
      ...window.VorMixin.search,
      ...window.VorMixin.delete,

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
})();
