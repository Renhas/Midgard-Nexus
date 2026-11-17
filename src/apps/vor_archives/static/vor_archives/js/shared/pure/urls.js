export function parseOverlayUrl(raw, baseOrigin) {
  if (!raw) {
    return "";
  }
  try {
    const url = new URL(raw, baseOrigin);
    return url.pathname + url.search;
  } catch (error) {
    return raw;
  }
}

export function isSamePageLink(href, target, location) {
  if (!href || (target && target !== "_self")) {
    return false;
  }
  try {
    const url = new URL(href, location.origin);
    return url.origin === location.origin && url.pathname === location.pathname && url.search === location.search;
  } catch (error) {
    return false;
  }
}
