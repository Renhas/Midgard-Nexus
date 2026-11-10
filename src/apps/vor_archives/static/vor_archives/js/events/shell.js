import { getAlpine } from "@lib/alpine";
import { closeOverlay, closeModal, overlayAlpine } from "@vor/common";
import { hasContent } from "@vor/shared/dom";

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
  }
});

document.body.addEventListener("vor:close-overlay", () => {
  closeOverlay();
  closeModal();
  getAlpine()?.store("vorArtworks")?.exitDeleteMode?.();
});

document.body.addEventListener("vor:close-modal", () => {
  closeModal();
});
