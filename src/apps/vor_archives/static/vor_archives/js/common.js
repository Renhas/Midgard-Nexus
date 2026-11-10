import { getAlpine } from "@lib/alpine";

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  if (el?.id === "vor-library-search-results") {
    getAlpine()?.initTree?.(el);
  }
  if (el?.id === "dash-heatmap" || el?.id === "dash-feed-more") {
    getAlpine()?.initTree?.(el);
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
