import { Sortable } from "@lib/sortable";
import { VorApi } from "@vor/artworks/api";

export const dragMixin = {
  reorderUrl: "",
  _sortable: null,
  _sortables: [],
  _artworkDragging: false,

  canDrag() {
    return !this.deleteMode;
  },
  canReorder() {
    return this.sortField === "custom" && !this.deleteMode;
  },
  destroySortables(list) {
    (list || []).forEach((sortable) => {
      try {
        sortable.destroy();
      } catch (error) {
        // already destroyed
      }
    });
  },
  setArtworkDragState(active) {
    this._artworkDragging = active;
    if (active) {
      document.body.dataset.dragging = this.viewMode === "grid" ? "grid" : "list";
    } else {
      delete document.body.dataset.dragging;
    }
  },
  setCollectionDragState(active) {
    this.collectionDragging = active;
    if (active) {
      document.body.dataset.dragging = "collections";
    } else {
      delete document.body.dataset.dragging;
    }
  },
  syncSortable() {
    this.destroySortables(this._sortables);
    this._sortables = [];
    if (this._sortable) {
      this._sortable.destroy();
      this._sortable = null;
    }
    if (!this.canDrag() || typeof Sortable === "undefined") {
      return;
    }
    const bindArtworkSortable = (container, allowSort) => {
      this._sortables.push(
        Sortable.create(container, {
          group: {
            name: "vor-artworks",
            pull: true,
            put: false,
          },
          sort: allowSort,
          animation: 150,
          draggable: ".vor-artwork-item",
          forceFallback: true,
          fallbackOnBody: true,
          fallbackTolerance: 4,
          ghostClass: "vor-artwork-item--ghost",
          chosenClass: "vor-artwork-item--chosen",
          dragClass: "vor-artwork-item--drag",
          filter: ".vor-artwork-row-delete, .vor-artwork-tile-delete, .vor-delete-check",
          preventOnFilter: true,
          onStart: () => {
            this.setArtworkDragState(true);
            this.closeMenu();
            window.getSelection?.().removeAllRanges();
          },
          onEnd: (evt) => {
            this.setArtworkDragState(false);
            this.clearCollectionDropTargets();
            const point = evt.originalEvent;
            const collectionId = this.collectionIdAtPoint(point?.clientX, point?.clientY);
            if (collectionId) {
              this.revertSortable(evt);
              this.addWorkToCollection(collectionId, evt.item?.dataset?.uwId);
              return;
            }
            const direct = document.getElementById("vor-artwork-list-items");
            if (allowSort && this.canReorder() && evt.from === direct && evt.to === direct) {
              this.saveOrder();
              return;
            }
            if (evt.from !== evt.to || evt.oldIndex !== evt.newIndex) {
              this.revertSortable(evt);
            }
          },
        }),
      );
    };
    const direct = document.getElementById("vor-artwork-list-items");
    if (direct) {
      bindArtworkSortable(direct, this.canReorder());
    }
    document.querySelectorAll(".vor-artwork-list-items-nested").forEach((container) => {
      bindArtworkSortable(container, false);
    });
  },
  revertSortable(evt) {
    if (!evt?.from || !evt.item) {
      return;
    }
    const siblings = [...evt.from.children].filter((node) => node !== evt.item);
    if (evt.oldIndex >= siblings.length) {
      evt.from.appendChild(evt.item);
      return;
    }
    evt.from.insertBefore(evt.item, siblings[evt.oldIndex]);
  },
  async saveOrder() {
    const container = document.getElementById("vor-artwork-list-items");
    if (!container) {
      return;
    }
    const ids = [...container.querySelectorAll(":scope > .vor-artwork-item")]
      .map((el) => el.dataset.uwId)
      .filter(Boolean);
    if (!this.sortAsc) {
      ids.reverse();
    }
    const url = this.collectionId ? this.collectionUrl(this.collectionId, "items/reorder/") : this.reorderUrl;
    if (!url) {
      return;
    }
    await VorApi.saveWorkOrder(url, ids);
  },
};
