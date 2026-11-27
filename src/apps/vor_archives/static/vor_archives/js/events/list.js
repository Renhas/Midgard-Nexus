import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";
import { vorNotify } from "@vor/shared/toasts";

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
    const item = event.target.closest(".vor-artwork-item");
    if (!item || event.target.closest(".vor-artwork-row__delete, .vor-artwork-tile__delete")) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const id = Number(item.dataset.uwId);
    if (id) {
      store.toggleSelected(id);
    }
  },
  true,
);

document.body.addEventListener("vor:reload-list", () => {
  getAlpine()?.store("vorArtworks")?.reloadList();
});

document.body.addEventListener("vor:reload-tree", () => {
  getAlpine()?.store("vorArtworks")?.reloadCollectionTree();
});

document.body.addEventListener("vor:collection-created", (event) => {
  const payload = event.detail?.value ?? event.detail;
  if (!payload) {
    return;
  }
  vorNotify.collectionCreated(payload, (id, name) => {
    getAlpine()?.store("vorArtworks")?.selectCollection(id, name);
  });
});

document.body.addEventListener("vor:collection-deleted", (event) => {
  const id = event.detail?.value ?? event.detail;
  getAlpine()?.store("vorArtworks")?.onCollectionDeleted(id);
  vorNotify.collectionDeleted();
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
  store.collectionPath = (store.collectionPath || []).map((part) =>
    String(part.id) === String(payload.id) ? { ...part, name: payload.name || part.name } : part,
  );
  vorNotify.collectionRenamed(payload.name);
});

document.body.addEventListener("vor:artworks-deleted", (event) => {
  const payload = event.detail?.value ?? event.detail;
  vorNotify.artworksDeleted(payload?.count ?? 1);
});

document.body.addEventListener("vor:work-saved", (event) => {
  const payload = event.detail?.value ?? event.detail;
  vorNotify.workSaved(payload?.title || "");
});

document.addEventListener("contextmenu", (event) => {
  const store = getAlpine()?.store("vorArtworks");
  if (!store || !document.getElementById("vor-artworks-opts")) {
    return;
  }
  const collectionItem = event.target.closest(".vor-collection-item");
  if (collectionItem) {
    event.preventDefault();
    store.openCollectionMenu(event, collectionItem);
    return;
  }
  const artwork = event.target.closest(".vor-artwork-row, .vor-artwork-tile");
  if (artwork) {
    event.preventDefault();
    store.openArtworkMenu(event, artwork.closest(".vor-artwork-item"));
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
  const sidebar = document.getElementById("sidebar-collections__list");
  const toggle = event.target.closest(".vor-collection-tree__toggle");
  if (toggle && sidebar?.contains(toggle)) {
    store.closeMenu();
    const id = toggle.closest(".vor-collection-tree__node")?.dataset.collectionId;
    if (id) {
      store.toggleCollectionExpanded(id);
    }
    return;
  }
  const collectionItem = event.target.closest(".vor-collection-item");
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

window.addEventListener(
  "scroll",
  (event) => {
    const menu = document.getElementById("vor-context-menu");
    if (menu && (menu === event.target || menu.contains(event.target))) {
      return;
    }
    getAlpine()?.store("vorArtworks")?.closeMenu();
  },
  true,
);

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  const isList = el?.id === "vor-artwork-list-body" || el?.id === "vor-artwork-list";
  const isTree = el?.id === "sidebar-collections__list";
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

document.addEventListener(
  "keydown",
  (event) => {
    if (!(event.ctrlKey || event.metaKey) || event.code !== "KeyF") {
      return;
    }
    if (!document.getElementById("vor-artworks-opts")) {
      return;
    }
    if (hasContent("vor-overlay") || hasContent("vor-modal")) {
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    getAlpine()?.store("vorArtworks")?.openSearch();
  },
  true,
);
