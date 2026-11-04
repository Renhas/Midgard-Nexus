(function () {
  window.VorMixin = window.VorMixin || {};

  window.VorMixin.delete = {
    deleteMode: false,
    selectedIds: [],

    syncSelectedDom() {
      document.querySelectorAll(".artwork-item").forEach((item) => {
        const selected = this.isSelected(item.dataset.uwId);
        item.querySelectorAll(".artwork-row, .artwork-tile").forEach((node) => {
          node.classList.toggle("is-selected", selected);
        });
        item.querySelectorAll(".custom-checkbox").forEach((node) => {
          node.classList.toggle("is-checked", selected);
        });
      });
    },
    enterDeleteMode() {
      this.deleteMode = true;
      this.selectedIds = [];
      this.applyListState();
    },
    exitDeleteMode() {
      this.deleteMode = false;
      this.selectedIds = [];
      this.applyListState();
    },
    toggleSelected(id) {
      id = Number(id);
      const index = this.selectedIds.indexOf(id);
      if (index > -1) {
        this.selectedIds.splice(index, 1);
      } else {
        this.selectedIds.push(id);
      }
      this.syncSelectedDom();
    },
    isSelected(id) {
      return this.selectedIds.includes(Number(id));
    },
    openPreview() {
      if (!this.selectedIds.length) {
        return;
      }
      const base =
        document.getElementById("vor-modal")?.dataset.vorDeletePreview;
      if (!base) {
        return;
      }
      const params = this.selectedIds.map((id) => `ids=${id}`).join("&");
      htmx.ajax("GET", `${base}?${params}`, {
        target: "#vor-modal",
        swap: "innerHTML",
      });
    },
  };
})();
