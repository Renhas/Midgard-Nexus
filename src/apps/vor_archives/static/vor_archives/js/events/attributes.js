import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";
import { closeModal } from "@vor/shared/modal";

document.body.addEventListener("vor:close-attr-modal", () => {
  closeModal();
  const store = getAlpine()?.store("vorAttributes");
  if (!store) {
    return;
  }
  store.exitDeleteMode();
  store.select("");
});

document.addEventListener("keydown", (event) => {
  if (!document.querySelector(".vor-attr-page")) {
    return;
  }
  const store = getAlpine()?.store("vorAttributes");
  if (!store?.deleteMode) {
    return;
  }
  if (event.key === "Escape" && !hasContent("vor-modal")) {
    store.exitDeleteMode();
    return;
  }
  if (event.key === "Enter" && store.selectedIds.length) {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
      return;
    }
    if (hasContent("vor-modal")) {
      return;
    }
    event.preventDefault();
    store.openPreview();
  }
});

document.addEventListener(
  "click",
  (event) => {
    const store = getAlpine()?.store("vorAttributes");
    if (!store?.deleteMode) {
      return;
    }
    const item = event.target.closest(".vor-attr-item");
    if (!item) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const id = item.dataset.attrId;
    if (id) {
      store.toggleSelected(id);
    }
  },
  true,
);
