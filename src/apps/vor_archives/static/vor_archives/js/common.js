import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";

export function syncPageScrollLock() {
  const locked = hasContent("vor-overlay")
    || Boolean(getAlpine()?.store("vorArtworks")?.searchOpen);
  document.documentElement.classList.toggle("vor-scroll-lock", locked);
};

export function overlayAlpine() {
  const el = document.querySelector("#vor-overlay .vor-overlay");
  const alpine = getAlpine();
  return el && alpine ? alpine.$data(el) : null;
};

export function overlayRequestPath(event) {
  const raw =
    event.detail.pathInfo?.requestPath ||
    event.detail.xhr?.responseURL ||
    "";
  try {
    const url = new URL(raw, window.location.origin);
    return url.pathname + url.search;
  } catch (error) {
    return raw;
  }
};

let _restoringOverlay = false;

export function pushOverlayHistory(event) {
  if (_restoringOverlay) {
    _restoringOverlay = false;
    return;
  }
  if (!hasContent("vor-overlay")) {
    return;
  }
  const overlayUrl = overlayRequestPath(event);
  if (!overlayUrl || history.state?.vorOverlay === overlayUrl) {
    return;
  }
  history.pushState({ vorOverlay: overlayUrl }, "", window.location.href);
};

export function restoreOverlay(overlayUrl) {
  _restoringOverlay = true;
  htmx.ajax("GET", overlayUrl, {
    target: "#vor-overlay",
    swap: "innerHTML",
  });
};

export function leaveOverlayOnCurrentPage() {
  if (!hasContent("vor-overlay")) {
    return false;
  }
  const proceed = () => {
    if (history.state?.vorOverlay) {
      history.pushState({}, "", window.location.href);
    }
    const el = document.getElementById("vor-overlay");
    if (el) {
      el.innerHTML = "";
    }
  };
  const data = overlayAlpine();
  if (data?.editing) {
    return data.tryLeave(proceed);
  }
  proceed();
  return true;
};

let _closingOverlay = false;

export function closeOverlay() {
  if (_closingOverlay) {
    return;
  }
  const data = overlayAlpine();
  if (data?.editing && data.dirtyChanges().length) {
    data.tryLeave(closeOverlay);
    return;
  }
  _closingOverlay = true;
  queueMicrotask(() => {
    _closingOverlay = false;
  });
  if (history.state && history.state.vorOverlay) {
    history.back();
    return;
  }
  const el = document.getElementById("vor-overlay");
  if (el) {
    el.innerHTML = "";
  }
};

export function closeModal() {
  const el = document.getElementById("vor-modal");
  if (el) {
    el.innerHTML = "";
  }
};

export function isSamePageLink(anchor) {
  if (!anchor?.href || anchor.target && anchor.target !== "_self") {
    return false;
  }
  try {
    const url = new URL(anchor.href, window.location.origin);
    return (
      url.origin === window.location.origin &&
      url.pathname === window.location.pathname &&
      url.search === window.location.search
    );
  } catch (error) {
    return false;
  }
};

export const SIDEBAR_STORAGE_KEY = "vor.artworks.sidebar";
export const ALL_WORK_TYPES = ["book", "film", "game"];
export const FILTER_KEYS = [
  "status", "age_rating", "tags", "genre_book", "genre_film", "genre_game", "platform",
];

export function mergeFilterSelection(allIds, savedSelected, savedKnown) {
  const catalog = allIds || [];
  if (!savedSelected && !savedKnown) {
    return [...catalog];
  }
  const selected = new Set((savedSelected || []).map(String));
  const known = new Set((savedKnown || []).map(String));
  return catalog.filter((id) => {
    const key = String(id);
    return !known.has(key) || selected.has(key);
  });
};

// popstate is a window-only event and does not bubble; must stay on window.
window.addEventListener("popstate", (event) => {
  const overlayUrl = event.state && event.state.vorOverlay;
  if (overlayUrl) {
    restoreOverlay(overlayUrl);
    return;
  }
  const el = document.getElementById("vor-overlay");
  if (el) {
    el.innerHTML = "";
  }
});

document.addEventListener(
  "click",
  (event) => {
    if (event.defaultPrevented || event.button !== 0) {
      return;
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    const anchor = event.target.closest("a[href]");
    if (!anchor || !hasContent("vor-overlay")) {
      return;
    }
    if (isSamePageLink(anchor)) {
      event.preventDefault();
      leaveOverlayOnCurrentPage();
      return;
    }
    const data = overlayAlpine();
    if (!data?.editing || !data.dirtyChanges().length) {
      return;
    }
    event.preventDefault();
    data.tryLeave(() => {
      window.location.href = anchor.href;
    });
  },
  true
);

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  if (el?.id === "vor-overlay") {
    pushOverlayHistory(event);
  }
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
