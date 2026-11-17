import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";

export function syncPageScrollLock() {
  const locked = hasContent("vor-overlay") || Boolean(getAlpine()?.store("vorArtworks")?.searchOpen);
  document.documentElement.classList.toggle("vor-scroll-lock", locked);
}

const overlayEl = document.getElementById("vor-overlay");
if (overlayEl) {
  new MutationObserver(syncPageScrollLock).observe(overlayEl, { childList: true });
}
