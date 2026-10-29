(function () {
  document.addEventListener("alpine:init", () => {
    Alpine.store("vorAttributes", {
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
        id = String(id);
        const index = this.selectedIds.indexOf(id);
        if (index > -1) {
          this.selectedIds.splice(index, 1);
        } else {
          this.selectedIds.push(id);
        }
      },
      isSelected(id) {
        return this.selectedIds.includes(String(id));
      },
      select(id) {
        this.selectedKey = id ? String(id) : "";
      },
      openPreview() {
        if (!this.selectedIds.length) {
          return;
        }
        const base =
          document.getElementById("vor-modal")?.dataset.vorAttrDeletePreview;
        if (!base) {
          return;
        }
        const params = this.selectedIds
          .map((id) => `ids=${encodeURIComponent(id)}`)
          .join("&");
        htmx.ajax("GET", `${base}?${params}`, {
          target: "#vor-modal",
          swap: "innerHTML",
        });
      },
      closeModal() {
        const el = document.getElementById("vor-modal");
        if (el) {
          el.innerHTML = "";
        }
      },
    });
  });

  document.body.addEventListener("vor:close-attr-modal", () => {
    const store = window.Alpine?.store("vorAttributes");
    if (!store) {
      return;
    }
    store.closeModal();
    store.exitDeleteMode();
    store.select("");
  });

  document.addEventListener("keydown", (event) => {
    const store = window.Alpine?.store("vorAttributes");
    if (!store) {
      return;
    }
    const attrPage = document.querySelector(".attr-page");
    if (!attrPage) {
      return;
    }
    if (event.key === "Escape") {
      if (window.hasContent("vor-modal")) {
        store.closeModal();
        return;
      }
      if (store.deleteMode) {
        store.exitDeleteMode();
      }
      return;
    }
    if (event.key === "Enter" && store.deleteMode && store.selectedIds.length) {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
        return;
      }
      if (window.hasContent("vor-modal")) {
        return;
      }
      event.preventDefault();
      store.openPreview();
    }
  });

  document.addEventListener(
    "click",
    (event) => {
      const store = window.Alpine?.store("vorAttributes");
      if (!store?.deleteMode) {
        return;
      }
      const item = event.target.closest(".attr-item");
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
    true
  );
})();
