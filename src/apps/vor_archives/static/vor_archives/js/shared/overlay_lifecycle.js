import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";
import { parseOverlayUrl, isSamePageLink } from "@vor/shared/pure/urls";

export function overlayAlpine() {
  const el = document.querySelector("#vor-overlay .vor-overlay");
  const alpine = getAlpine();
  return el && alpine ? alpine.$data(el) : null;
}

function overlayRequestPath(event) {
  const raw = event.detail.pathInfo?.requestPath || event.detail.xhr?.responseURL || "";
  return parseOverlayUrl(raw, window.location.origin);
}

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
}

export function restoreOverlay(overlayUrl) {
  _restoringOverlay = true;
  htmx.ajax("GET", overlayUrl, {
    target: "#vor-overlay",
    swap: "innerHTML",
  });
}

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
}

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
}

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
    if (isSamePageLink(anchor.href, anchor.target, window.location)) {
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
  true,
);

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.elt?.id === "vor-overlay") {
    pushOverlayHistory(event);
  }
});
