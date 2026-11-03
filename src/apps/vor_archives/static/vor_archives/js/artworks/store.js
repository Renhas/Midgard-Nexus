(function () {
  /* ============================================
     Domain mixin: search overlay and delete mode
     ============================================ */
  const searchAndDeleteMixin = {
    searchUrl: "",
    attachUrl: "",
    searchOpen: false,
    searchQuery: "",
    searchTimer: null,
    deleteMode: false,
    selectedIds: [],

    syncSelectedDom() {
      document.querySelectorAll(".artwork-item").forEach((item) => {
        const selected = this.isSelected(item.dataset.uwId);
        item.querySelectorAll(".artwork-row, .artwork-tile").forEach((node) => {
          node.classList.toggle("is-selected", selected);
        });
        item.querySelectorAll(".custom-checkbox").forEach((node) => {
          node.classList.toggle("is-checked", selected);
        });
      });
    },
    openSearch() {
      if (this.searchOpen) {
        document.getElementById("vor-library-search-input")?.focus();
        return;
      }
      this.searchOpen = true;
      window.syncPageScrollLock();
      this.searchQuery = "";
      const results = document.getElementById("vor-library-search-results");
      if (results) {
        results.innerHTML = "";
      }
      queueMicrotask(() => document.getElementById("vor-library-search-input")?.focus());
    },
    closeSearch() {
      this.searchOpen = false;
      window.syncPageScrollLock();
      this.searchQuery = "";
      const results = document.getElementById("vor-library-search-results");
      if (results) {
        results.innerHTML = "";
      }
    },
    onSearchInput() {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.runSearch(), 280);
    },
    runSearch() {
      const query = String(this.searchQuery || "").trim();
      const results = document.getElementById("vor-library-search-results");
      if (!query || !this.searchUrl) {
        if (results) {
          results.innerHTML = "";
        }
        return;
      }
      htmx.ajax("GET", `${this.searchUrl}?q=${encodeURIComponent(query)}`, {
        target: "#vor-library-search-results",
        swap: "innerHTML",
      });
    },
    async attachFromSearch(typeKey, workId) {
      const data = await VorApi.attachWorkFromSearch(
        this.attachUrl, typeKey, workId,
      );
      if (!data?.ok) return;
      this.reloadList();
      this.runSearch();
    },
    openWork(url) {
      this.closeSearch();
      htmx.ajax("GET", url, {
        target: "#vor-overlay",
        swap: "innerHTML",
      });
    },

    enterDeleteMode() {
      this.deleteMode = true;
      this.selectedIds = [];
      this.applyListState();
    },
    exitDeleteMode() {
      this.deleteMode = false;
      this.selectedIds = [];
      this.applyListState();
    },
    toggleSelected(id) {
      id = Number(id);
      const index = this.selectedIds.indexOf(id);
      if (index > -1) {
        this.selectedIds.splice(index, 1);
      } else {
        this.selectedIds.push(id);
      }
      this.syncSelectedDom();
    },
    isSelected(id) {
      return this.selectedIds.includes(Number(id));
    },
    openPreview() {
      if (!this.selectedIds.length) {
        return;
      }
      const base =
        document.getElementById("vor-modal")?.dataset.vorDeletePreview;
      if (!base) {
        return;
      }
      const params = this.selectedIds.map((id) => `ids=${id}`).join("&");
      htmx.ajax("GET", `${base}?${params}`, {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
  };

  /* ============================================
     Base: composition + lifecycle + cross-cutting
     ============================================ */
  document.addEventListener("alpine:init", () => {
    Alpine.store("vorArtworks", {
      isStaff: false,
      _booted: false,

      ...window.VorMixin.filters,
      ...window.VorMixin.collections,
      ...window.VorMixin.drag,
      ...window.VorMixin.menu,
      ...searchAndDeleteMixin,

      initFromPage(opts) {
        if (this._booted) return;
        this._booted = true;

        // filtersMixin
        this.listUrl = opts.listUrl || "";
        this.filterCatalog = { ...this.filterCatalog, ...(opts.filterCatalog || {}) };

        // collectionsMixin
        this.collectionTreeUrl = opts.collectionTreeUrl || "";
        this.collectionReorderUrl = opts.collectionReorderUrl || "";

        // dragMixin
        this.reorderUrl = opts.reorderUrl || "";

        // searchAndDeleteMixin
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
