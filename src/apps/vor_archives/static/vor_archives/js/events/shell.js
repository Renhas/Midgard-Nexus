import { getAlpine } from "@lib/alpine";
import { closeModal } from "@vor/shared/modal";
import { hasContent } from "@vor/shared/dom";
import { closeOverlay, overlayAlpine } from "@vor/shared/overlay_lifecycle";

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") {
    return;
  }
  const store = getAlpine()?.store("vorArtworks");
  if (store?.menu?.open) {
    store.closeMenu();
    return;
  }
  if (store?.searchOpen) {
    store.closeSearch();
    return;
  }
  if (hasContent("vor-modal")) {
    closeModal();
    return;
  }
  const overlay = overlayAlpine();
  if (overlay?.attachOpen) {
    overlay.attachOpen = false;
    return;
  }
  if (overlay?.phase && overlay.phase !== "form") {
    overlay.dismissModal();
    return;
  }
  if (hasContent("vor-overlay")) {
    closeOverlay();
    return;
  }
  if (store?.deleteMode) {
    store.exitDeleteMode();
    return;
  }
  const attrStore = getAlpine()?.store("vorAttributes");
  if (attrStore?.deleteMode) {
    attrStore.exitDeleteMode();
  }
});

document.body.addEventListener("vor:close-overlay", () => {
  closeOverlay();
  queueMicrotask(closeModal);
  getAlpine()?.store("vorArtworks")?.exitDeleteMode?.();
});

document.body.addEventListener("vor:close-modal", () => {
  queueMicrotask(closeModal);
});
