(function () {
  /* ============================================
     Domain mixin: context menu and flyout
     ============================================ */
  const menuMixin = {
    menu: {
      open: false, kind: "", x: 0, y: 0,
      collectionId: null, collectionName: "",
      uwId: null, detailUrl: "",
      flyout: false, flyoutSide: "right", flyoutX: 0, flyoutY: 0,
      membership: [], membershipLoading: false,
      canNudgeUp: false, canNudgeDown: false,
      canLevelUp: false, canLevelDown: false,
      canRemoveFromCollection: false,
    },
    _flyoutTimer: null,

    placeMenu(x, y) {
      this.menu.x = x;
      this.menu.y = y;
      this.menu.open = true;
      queueMicrotask(() => {
        const el = document.getElementById("vor-context-menu");
        if (!el) {
          return;
        }
        const rect = el.getBoundingClientRect();
        const pad = 8;
        let nextX = x;
        let nextY = y;
        if (nextX + rect.width > window.innerWidth - pad) {
          nextX = window.innerWidth - rect.width - pad;
        }
        if (nextY + rect.height > window.innerHeight - pad) {
          nextY = window.innerHeight - rect.height - pad;
        }
        this.menu.x = Math.max(pad, nextX);
        this.menu.y = Math.max(pad, nextY);
      });
    },
    closeMenu() {
      this.menu.open = false;
      this.menu.flyout = false;
      this.menu.membership = [];
      this.menu.canRemoveFromCollection = false;
      this.cancelCloseFlyout();
    },
    openCollectionMenu(event, el) {
      this.closeMenu();
      this.menu.kind = "collection";
      this.menu.collectionId = Number(el.dataset.collectionId);
      this.menu.collectionName = el.dataset.collectionName || "";
      const node = el.closest(".collection-tree-node");
      const siblings = this.collectionSiblings(node);
      const index = siblings.indexOf(node);
      this.menu.canNudgeUp = index > 0;
      this.menu.canNudgeDown = index >= 0 && index < siblings.length - 1;
      this.menu.canLevelUp = Boolean(node?.parentElement?.closest(".collection-tree-node"));
      this.menu.canLevelDown = index > 0;
      this.placeMenu(event.clientX, event.clientY);
    },
    openArtworkMenu(event, item) {
      if (!item || this.deleteMode) {
        return;
      }
      this.closeMenu();
      this.menu.kind = "artwork";
      this.menu.uwId = Number(item.dataset.uwId);
      this.menu.detailUrl = item.dataset.detailUrl || "";
      const nested = Boolean(item.closest(".artwork-list-items-nested"));
      const list = document.getElementById("artwork-list-items");
      const items = list
        ? [...list.querySelectorAll(":scope > .artwork-item")]
        : [];
      const index = items.indexOf(item);
      const canNudge = !nested && this.canReorder() && index >= 0;
      this.menu.canNudgeUp = canNudge && index > 0;
      this.menu.canNudgeDown = canNudge && index < items.length - 1;
      this.menu.canLevelUp = false;
      this.menu.canLevelDown = false;
      this.menu.canRemoveFromCollection = Boolean(this.collectionId) && !nested;
      this.placeMenu(event.clientX, event.clientY);
      this.loadArtworkCollections();
    },
    nudgeArtwork(delta) {
      const item = document.querySelector(
        `.artwork-item[data-uw-id="${this.menu.uwId}"]`,
      );
      const list = document.getElementById("artwork-list-items");
      this.closeMenu();
      if (!item || !list || item.closest(".artwork-list-items-nested")) {
        return;
      }
      const items = [...list.querySelectorAll(":scope > .artwork-item")];
      const index = items.indexOf(item);
      const next = index + Number(delta);
      if (index < 0 || next < 0 || next >= items.length) {
        return;
      }
      if (delta > 0) {
        items[next].after(item);
      } else {
        items[next].before(item);
      }
      this.saveOrder();
    },
    nudgeCollection(delta) {
      const node = this.collectionNode(this.menu.collectionId);
      this.closeMenu();
      if (!node) {
        return;
      }
      const siblings = this.collectionSiblings(node);
      const index = siblings.indexOf(node);
      const next = index + Number(delta);
      if (index < 0 || next < 0 || next >= siblings.length) {
        return;
      }
      if (delta > 0) {
        siblings[next].after(node);
      } else {
        siblings[next].before(node);
      }
      this.postCollectionMove(node);
    },
    shiftCollectionLevel(direction) {
      const node = this.collectionNode(this.menu.collectionId);
      this.closeMenu();
      if (!node) {
        return;
      }
      const siblings = this.collectionSiblings(node);
      const index = siblings.indexOf(node);
      if (direction > 0) {
        const prev = index > 0 ? siblings[index - 1] : null;
        const children = prev?.querySelector(":scope > .collection-children");
        if (!prev || !children) {
          return;
        }
        this.setCollectionExpanded(prev.dataset.collectionId, true);
        children.appendChild(node);
        this.postCollectionMove(node);
        return;
      }
      const parentNode = node.parentElement?.closest(".collection-tree-node");
      if (!parentNode) {
        return;
      }
      parentNode.after(node);
      this.postCollectionMove(node);
    },
    async loadArtworkCollections() {
      if (!this.menu.uwId || !this.listUrl) return;
      this.menu.membershipLoading = true;
      const data = await VorApi.listArtworkCollections(this.listUrl, this.menu.uwId);
      this.menu.membership = this.flattenCollectionTree(data?.tree || []);
      this.menu.membershipLoading = false;
    },
    openCollectionFlyout() {
      this.cancelCloseFlyout();
      this.menu.flyout = true;
      const menu = document.getElementById("vor-context-menu");
      const trigger = menu?.querySelector(".has-submenu");
      const rect = (trigger || menu)?.getBoundingClientRect();
      if (!rect) {
        return;
      }
      const width = 220;
      const spaceRight = window.innerWidth - rect.right;
      this.menu.flyoutSide = spaceRight > width ? "right" : "left";
      this.menu.flyoutX = spaceRight > width ? rect.right : rect.left - width;
      this.menu.flyoutY = rect.top;
    },
    toggleCollectionFlyout() {
      if (this.menu.flyout) {
        this.menu.flyout = false;
        return;
      }
      this.openCollectionFlyout();
    },
    scheduleCloseFlyout() {
      this.cancelCloseFlyout();
      this._flyoutTimer = window.setTimeout(() => {
        this.menu.flyout = false;
      }, 180);
    },
    cancelCloseFlyout() {
      if (this._flyoutTimer) {
        window.clearTimeout(this._flyoutTimer);
        this._flyoutTimer = null;
      }
    },
    async removeFromCurrentCollection() {
      const collectionId = this.collectionId;
      const uwId = this.menu.uwId;
      this.closeMenu();
      if (!collectionId || !uwId) return;
      const data = await VorApi.removeWorkFromCollection(
        this.collectionUrl(collectionId, "items/"),
        uwId,
      );
      if (!data?.ok) return;
      window.dispatchEvent(new Event("collection-update"));
      this.reloadList();
    },
    async toggleWorkCollection(item) {
      if (!item || !this.menu.uwId) return;
      const adding = !item.in_collection;
      const data = await VorApi.toggleWorkCollection(
        this.collectionUrl(item.id, "items/"),
        this.menu.uwId,
        adding,
      );
      if (!data?.ok) return;
      item.in_collection = adding;
      window.dispatchEvent(new Event("collection-update"));
      this.reloadList();
    },
    menuRenameCollection() {
      const id = this.menu.collectionId;
      this.closeMenu();
      if (!id) {
        return;
      }
      htmx.ajax("GET", this.collectionUrl(id, "edit/"), {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
    menuDeleteCollection() {
      const id = this.menu.collectionId;
      this.closeMenu();
      if (!id) {
        return;
      }
      htmx.ajax("GET", this.collectionUrl(id, "delete/preview/"), {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
    menuEditArtwork() {
      let url = this.menu.detailUrl;
      this.closeMenu();
      if (!url) {
        return;
      }
      if (this.isStaff) {
        url += (url.includes("?") ? "&" : "?") + "edit=1";
      }
      htmx.ajax("GET", url, {
        target: "#vor-overlay",
        swap: "innerHTML",
      });
    },
    menuDeleteArtwork() {
      const id = this.menu.uwId;
      const base = document.getElementById("vor-modal")?.dataset.vorDeletePreview;
      this.closeMenu();
      if (!id || !base) {
        return;
      }
      htmx.ajax("GET", `${base}?ids=${id}`, {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
    onCollectionDeleted(id) {
      if (String(this.collectionId) === String(id)) {
        this.selectLibrary();
      }
    },
  };

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
      ...menuMixin,
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
