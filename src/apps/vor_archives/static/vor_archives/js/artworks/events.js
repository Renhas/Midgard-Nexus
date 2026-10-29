(function () {
  document.addEventListener("keydown", (event) => {
    const store = window.Alpine?.store("vorArtworks");
    if (!store) {
      return;
    }
    if (event.key === "Escape") {
      if (store.menu?.open) {
        store.closeMenu();
        return;
      }
      if (store.searchOpen) {
        store.closeSearch();
        return;
      }
      if (window.hasContent("vor-modal")) {
        store.closeModal();
        return;
      }
      const overlay = window.overlayAlpine();
      if (overlay?.attachOpen) {
        overlay.attachOpen = false;
        return;
      }
      if (overlay?.phase && overlay.phase !== "form") {
        overlay.dismissModal();
        return;
      }
      if (window.hasContent("vor-overlay")) {
        store.closeOverlay();
        return;
      }
      if (store.deleteMode) {
        store.exitDeleteMode();
      }
      return;
    }
    if (event.key === "Enter" && store.deleteMode && store.selectedIds.length) {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
        return;
      }
      if (window.hasContent("vor-modal") || window.hasContent("vor-overlay")) {
        return;
      }
      event.preventDefault();
      store.openPreview();
    }
  });

  document.addEventListener(
    "click",
    (event) => {
      const store = window.Alpine?.store("vorArtworks");
      if (!store?.deleteMode) {
        return;
      }
      const item = event.target.closest(".artwork-item");
      if (!item || event.target.closest(".artwork-row-delete, .artwork-tile-delete")) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const id = Number(item.dataset.uwId);
      if (id) {
        store.toggleSelected(id);
      }
    },
    true
  );

  document.body.addEventListener("vor:close-overlay", () => {
    const store = window.Alpine?.store("vorArtworks");
    if (!store) {
      return;
    }
    store.closeOverlay();
    store.closeModal();
    store.exitDeleteMode();
  });

  document.body.addEventListener("vor:reload-list", () => {
    window.Alpine?.store("vorArtworks")?.reloadList();
  });

  document.body.addEventListener("vor:reload-tree", () => {
    window.Alpine?.store("vorArtworks")?.reloadCollectionTree();
  });

  document.body.addEventListener("vor:close-modal", () => {
    window.Alpine?.store("vorArtworks")?.closeModal();
  });

  document.body.addEventListener("vor:collection-deleted", (event) => {
    const id = event.detail?.value ?? event.detail;
    window.Alpine?.store("vorArtworks")?.onCollectionDeleted(id);
  });

  document.body.addEventListener("vor:collection-renamed", (event) => {
    const payload = event.detail?.value ?? event.detail;
    const store = window.Alpine?.store("vorArtworks");
    if (!store || !payload) {
      return;
    }
    if (String(store.collectionId) === String(payload.id)) {
      store.collectionName = payload.name || store.collectionName;
    }
    store.collectionPath = (store.collectionPath || []).map((part) => (
      String(part.id) === String(payload.id)
        ? { ...part, name: payload.name || part.name }
        : part
    ));
  });

  document.addEventListener("contextmenu", (event) => {
    const store = window.Alpine?.store("vorArtworks");
    if (!store || !document.getElementById("vor-artworks-opts")) {
      return;
    }
    const collectionItem = event.target.closest(".collection-item");
    if (collectionItem) {
      event.preventDefault();
      store.openCollectionMenu(event, collectionItem);
      return;
    }
    const artwork = event.target.closest(".artwork-row, .artwork-tile");
    if (artwork) {
      event.preventDefault();
      store.openArtworkMenu(event, artwork.closest(".artwork-item"));
    }
  });

  document.addEventListener("pointermove", (event) => {
    const store = window.Alpine?.store("vorArtworks");
    if (store?._artworkDragging || store?.collectionDragging) {
      store.highlightCollectionAtPoint(event.clientX, event.clientY);
    }
  });

  document.addEventListener("click", (event) => {
    const store = window.Alpine?.store("vorArtworks");
    if (!store) {
      return;
    }
    const sidebar = document.getElementById("sidebar-collections-list");
    const toggle = event.target.closest(".collection-toggle");
    if (toggle && sidebar?.contains(toggle)) {
      store.closeMenu();
      const id = toggle.closest(".collection-tree-node")?.dataset.collectionId;
      if (id) {
        store.toggleCollectionExpanded(id);
      }
      return;
    }
    const collectionItem = event.target.closest(".collection-item");
    if (collectionItem && sidebar?.contains(collectionItem)) {
      store.closeMenu();
      store.selectCollectionFromEl(collectionItem);
      return;
    }
    if (!store.menu?.open) {
      return;
    }
    if (event.target.closest("#vor-context-menu")) {
      return;
    }
    store.closeMenu();
  });

  window.addEventListener("scroll", (event) => {
    const menu = document.getElementById("vor-context-menu");
    if (menu && (menu === event.target || menu.contains(event.target))) {
      return;
    }
    window.Alpine?.store("vorArtworks")?.closeMenu();
  }, true);
})();
