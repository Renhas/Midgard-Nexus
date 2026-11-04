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
      closeOverlay() {
        if (this._closingOverlay) {
          return;
        }
        const data = window.overlayAlpine();
        if (data?.editing && data.dirtyChanges().length) {
          data.tryLeave(() => this.closeOverlay());
          return;
        }
        this._closingOverlay = true;
        queueMicrotask(() => {
          this._closingOverlay = false;
        });
        if (history.state && history.state.vorOverlay) {
          history.back();
          return;
        }
        const el = document.getElementById("vor-overlay");
        if (el) {
          el.innerHTML = "";
        }
      },
      closeModal() {
        const el = document.getElementById("vor-modal");
        if (el) {
          el.innerHTML = "";
        }
      },
    });
  });
})();
