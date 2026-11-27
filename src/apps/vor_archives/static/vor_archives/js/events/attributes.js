import { getAlpine } from "@lib/alpine";
import { hasContent } from "@vor/shared/dom";
import { closeModal } from "@vor/shared/modal";
import { vorNotify } from "@vor/shared/toasts";

document.body.addEventListener("vor:attr-saved", (event) => {
  const payload = event.detail?.value ?? event.detail;
  if (payload) {
    vorNotify.attrSaved(payload);
  }
});

document.body.addEventListener("vor:attr-deleted", (event) => {
  const payload = event.detail?.value ?? event.detail;
  vorNotify.attrsDeleted(payload?.count ?? 1);
});

document.body.addEventListener("vor:close-attr-modal", () => {
  queueMicrotask(closeModal);
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
