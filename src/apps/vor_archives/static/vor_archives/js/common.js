import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";

export function syncPageScrollLock() {
  const locked = hasContent("vor-overlay")
    || Boolean(getAlpine()?.store("vorArtworks")?.searchOpen);
  document.documentElement.classList.toggle("vor-scroll-lock", locked);
};


export function closeModal() {
  const el = document.getElementById("vor-modal");
  if (el) {
    el.innerHTML = "";
  }
};


document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  if (el?.id === "vor-library-search-results") {
    getAlpine()?.initTree?.(el);
  }
  if (el?.id === "vor-modal") {
    getAlpine()?.initTree?.(el);
  }
  if (el?.id === "dash-heatmap" || el?.id === "dash-feed-more") {
    getAlpine()?.initTree?.(el);
  }
  syncPageScrollLock();
});

const overlayEl = document.getElementById("vor-overlay");
if (overlayEl) {
  new MutationObserver(syncPageScrollLock).observe(overlayEl, { childList: true });
}

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
