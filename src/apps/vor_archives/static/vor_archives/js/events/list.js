import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";

document.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }
  const store = getAlpine()?.store("vorArtworks");
  if (!store?.deleteMode || !store.selectedIds.length) {
    return;
  }
  if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
    return;
  }
  if (hasContent("vor-modal") || hasContent("vor-overlay")) {
    return;
  }
  event.preventDefault();
  store.openPreview();
});

document.addEventListener(
  "click",
  (event) => {
    const store = getAlpine()?.store("vorArtworks");
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

document.body.addEventListener("vor:reload-list", () => {
  getAlpine()?.store("vorArtworks")?.reloadList();
});

document.body.addEventListener("vor:reload-tree", () => {
  getAlpine()?.store("vorArtworks")?.reloadCollectionTree();
});

document.body.addEventListener("vor:collection-deleted", (event) => {
  const id = event.detail?.value ?? event.detail;
  getAlpine()?.store("vorArtworks")?.onCollectionDeleted(id);
});

document.body.addEventListener("vor:collection-renamed", (event) => {
  const payload = event.detail?.value ?? event.detail;
  const store = getAlpine()?.store("vorArtworks");
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
  const store = getAlpine()?.store("vorArtworks");
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
  const store = getAlpine()?.store("vorArtworks");
  if (store?._artworkDragging || store?.collectionDragging) {
    store.highlightCollectionAtPoint(event.clientX, event.clientY);
  }
});

document.addEventListener("click", (event) => {
  const store = getAlpine()?.store("vorArtworks");
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
  getAlpine()?.store("vorArtworks")?.closeMenu();
}, true);

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  const isList = el?.id === "artwork-list-body" || el?.id === "artwork-list";
  const isTree = el?.id === "sidebar-collections-list";
  if (!isList && !isTree) return;
  const store = getAlpine()?.store("vorArtworks");
  if (!store) return;

  if (isList) {
    getAlpine()?.initTree?.(el);
    store.applyListState();
  }
  if (isTree) {
    getAlpine()?.destroyTree?.(el);
    getAlpine()?.initTree?.(el);
    store.pruneExpandedCollections();
    store.applyCollectionTreeState();
    store.syncCollectionSortable();
    store.refreshCollectionPath();
  }
});

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.elt?.id === "vor-library-search-results") {
    getAlpine()?.initTree?.(event.detail.elt);
  }
});

document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey) || event.code !== "KeyF") {
    return;
  }
  if (!document.getElementById("vor-artworks-opts")) {
    return;
  }
  if (hasContent("vor-overlay")) {
    return;
  }
  event.preventDefault();
  event.stopImmediatePropagation();
  getAlpine()?.store("vorArtworks")?.openSearch();
}, true);
