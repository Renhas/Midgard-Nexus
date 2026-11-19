import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { buildDeletePreviewUrl, hasSelectedId, toggleSelectedId } from "@vor/attributes/pure/selection";

document.addEventListener("alpine:init", () => {
  getAlpine().store("vorAttributes", {
    deleteMode: false,
    selectedIds: [],
    selectedKey: "",

    enterDeleteMode() {
      this.deleteMode = true;
      this.selectedIds = [];
    },
    exitDeleteMode() {
      this.deleteMode = false;
      this.selectedIds = [];
    },
    toggleSelected(id) {
      this.selectedIds = toggleSelectedId(this.selectedIds, id);
    },
    isSelected(id) {
      return hasSelectedId(this.selectedIds, id);
    },
    select(id) {
      this.selectedKey = id ? String(id) : "";
    },
    openPreview() {
      const base = document.getElementById("vor-modal")?.dataset.vorAttrDeletePreview;
      const url = buildDeletePreviewUrl(base, this.selectedIds);
      if (!url) {
        return;
      }
      htmx.ajax("GET", url, {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
  });
});
