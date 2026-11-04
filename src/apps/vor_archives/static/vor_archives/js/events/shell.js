(function () {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    const store = window.Alpine?.store("vorArtworks");
    if (store?.menu?.open) {
      store.closeMenu();
      return;
    }
    if (store?.searchOpen) {
      store.closeSearch();
      return;
    }
    if (window.hasContent("vor-modal")) {
      window.closeModal();
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
      window.closeOverlay();
      return;
    }
    if (store?.deleteMode) {
      store.exitDeleteMode();
    }
  });

  document.body.addEventListener("vor:close-overlay", () => {
    window.closeOverlay();
    window.closeModal();
    window.Alpine?.store("vorArtworks")?.exitDeleteMode?.();
  });

  document.body.addEventListener("vor:close-modal", () => {
    window.closeModal();
  });
})();
