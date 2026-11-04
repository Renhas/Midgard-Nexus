(function () {
  window.VorMixin = window.VorMixin || {};

  window.VorMixin.collections = {
    collectionTreeUrl: "",
    collectionReorderUrl: "",
    collectionId: null,
    collectionName: "",
    collectionPath: [],
    collectionDragging: false,
    expandedCollectionIds: [],
    _collectionSortables: [],
    _collectionJustDragged: false,
    _pendingNestId: "",
    _dragCollectionId: "",

    collectionUrl(id, rest = "") {
      return window.getCollectionUrl(this.collectionBaseUrl, id, rest);
    },
    selectLibrary() {
      this.collectionId = null;
      this.collectionName = "";
      this.collectionPath = [];
      this.reloadList();
      this.applyCollectionTreeState();
    },
    collectionPathFromTree(id) {
      return window.getCollectionPathFromTree(id);
    },
    refreshCollectionPath() {
      if (!this.collectionId) {
        this.collectionPath = [];
        return;
      }
      const path = this.collectionPathFromTree(this.collectionId);
      if (path.length) {
        this.collectionPath = path;
        this.collectionName = path[path.length - 1].name;
      }
    },
    selectCollection(id, name) {
      this.collectionId = Number(id) || null;
      this.collectionName = name || "";
      this.collectionPath = this.collectionId
        ? this.collectionPathFromTree(this.collectionId)
        : [];
      if (!this.collectionPath.length && this.collectionId) {
        this.collectionPath = [{
          id: this.collectionId,
          name: this.collectionName || "Коллекция",
        }];
      } else if (this.collectionPath.length) {
        this.collectionName = this.collectionPath[this.collectionPath.length - 1].name;
      }
      this.collectionPath.slice(0, -1).forEach((part) => {
        this.setCollectionExpanded(part.id, true);
      });
      this.reloadList();
      this.applyCollectionTreeState();
    },
    selectCollectionFromEl(el) {
      if (!el || this._collectionJustDragged) {
        return;
      }
      this.selectCollection(el.dataset.collectionId, el.dataset.collectionName);
    },
    isCollectionExpanded(id) {
      return this.expandedCollectionIds.includes(Number(id));
    },
    setCollectionExpanded(id, value) {
      id = Number(id);
      const index = this.expandedCollectionIds.indexOf(id);
      if (value && index < 0) {
        this.expandedCollectionIds.push(id);
      } else if (!value && index > -1) {
        this.expandedCollectionIds.splice(index, 1);
      }
    },
    toggleCollectionExpanded(id) {
      this.setCollectionExpanded(id, !this.isCollectionExpanded(id));
      this.applyCollectionExpandState();
    },
    applyCollectionExpandState() {
      document.querySelectorAll(".collection-tree-node").forEach((node) => {
        const expanded = this.isCollectionExpanded(node.dataset.collectionId);
        node.classList.toggle("is-expanded", expanded);
        node.querySelector(":scope > .collection-item .bi-chevron-right")
          ?.classList.toggle("bi-rotate-90", expanded);
      });
    },
    applyCollectionTreeState() {
      document.querySelectorAll(".collection-item").forEach((item) => {
        item.classList.toggle(
          "is-active",
          String(this.collectionId || "") === String(item.dataset.collectionId || ""),
        );
      });
      this.applyCollectionExpandState();
    },
    reloadCollectionTree() {
      if (!this.collectionTreeUrl) {
        return;
      }
      htmx.ajax("GET", this.collectionTreeUrl, {
        target: "#sidebar-collections-list",
        swap: "innerHTML",
      });
    },
    pruneExpandedCollections() {
      this.expandedCollectionIds = this.expandedCollectionIds.filter((id) => {
        const node = document.querySelector(
          `.collection-tree-node[data-collection-id="${id}"]`,
        );
        if (!node) {
          return false;
        }
        return Boolean(node.querySelector(
          ":scope > .collection-children > .collection-tree-node",
        ));
      });
    },
    collectionNode(id) {
      return window.getCollectionNode(id);
    },
    collectionSiblings(node) {
      return window.getCollectionSiblings(node);
    },
    async postCollectionMove(node) {
      const parentEl = node?.parentElement;
      if (!node || !parentEl || !this.collectionReorderUrl) {
        return;
      }
      try {
        await VorApi.moveCollection(this.collectionReorderUrl, {
          id: node.dataset.collectionId || "",
          parent_id: parentEl.dataset.parentId || "",
          sibling_ids: this.collectionSiblings(node)
            .map((sibling) => sibling.dataset.collectionId)
            .filter(Boolean),
        });
      } finally {
        this.reloadCollectionTree();
      }
    },
    syncCollectionSortable() {
      this.destroySortables(this._collectionSortables);
      this._collectionSortables = [];
      if (typeof Sortable === "undefined") {
        return;
      }
      const root = document.getElementById("collection-tree-root");
      if (!root) {
        return;
      }
      const containers = [root, ...root.querySelectorAll(".collection-children")];
      containers.forEach((container) => {
        this._collectionSortables.push(Sortable.create(container, {
          group: "vor-collections",
          animation: 150,
          draggable: ".collection-tree-node",
          handle: ".collection-item",
          direction: "vertical",
          forceFallback: true,
          fallbackOnBody: true,
          fallbackTolerance: 4,
          invertSwap: true,
          invertSwapThreshold: 0.45,
          swapThreshold: 0.65,
          emptyInsertThreshold: 6,
          ghostClass: "is-sortable-ghost",
          chosenClass: "is-sortable-chosen",
          dragClass: "is-sortable-drag",
          filter: ".collection-toggle",
          preventOnFilter: false,
          onMove: (evt, originalEvent) => {
            const target = evt.to;
            if (target?.classList.contains("collection-children")) {
              const parentId = target.dataset.parentId;
              if (parentId && !this.isCollectionExpanded(parentId)) {
                return false;
              }
            }
            if (this.markCollectionNestZone(
              originalEvent?.clientX,
              originalEvent?.clientY,
              evt.dragged,
            )) {
              return false;
            }
            return true;
          },
          onStart: (evt) => {
            this.setCollectionDragState(true);
            this._pendingNestId = "";
            this._dragCollectionId = evt.item?.dataset?.collectionId || "";
            if (evt.item) {
              evt.item.style.pointerEvents = "none";
            }
            this.closeMenu();
          },
          onEnd: (evt) => {
            if (evt.item) {
              evt.item.style.pointerEvents = "";
            }
            this.setCollectionDragState(false);
            this._collectionJustDragged = true;
            window.setTimeout(() => {
              this._collectionJustDragged = false;
            }, 80);
            const pendingId = this._pendingNestId;
            this.clearCollectionDropTargets();
            this._pendingNestId = "";
            this._dragCollectionId = "";
            if (pendingId && this.nestCollectionInto(evt.item, pendingId)) {
              return;
            }
            this.saveCollectionTree(evt);
          },
        }));
      });
    },
    saveCollectionTree(evt) {
      const item = evt?.item;
      if (!item) {
        return;
      }
      this.postCollectionMove(item);
    },
    collectionIdAtPoint(x, y) {
      if (x == null || y == null) {
        return null;
      }
      const el = document.elementFromPoint(x, y);
      return el?.closest(".collection-item")?.dataset?.collectionId || null;
    },
    clearCollectionDropTargets() {
      document.querySelectorAll(".collection-item.is-drop-target").forEach((node) => {
        node.classList.remove("is-drop-target");
      });
    },
    highlightCollectionAtPoint(x, y) {
      if (this.collectionDragging) {
        this.markCollectionNestZone(x, y);
        return;
      }
      this.clearCollectionDropTargets();
      const id = this.collectionIdAtPoint(x, y);
      if (!id || id === this._dragCollectionId) {
        return;
      }
      document.querySelector(
        `.collection-item[data-collection-id="${id}"]`,
      )?.classList.add("is-drop-target");
    },
    collectionRowAtPoint(x, y, dragged) {
      if (x == null || y == null) {
        return null;
      }
      const blockers = [];
      if (dragged) {
        blockers.push(dragged);
      }
      document.querySelectorAll(".is-sortable-ghost, .is-sortable-drag, .sortable-fallback").forEach((node) => {
        blockers.push(node);
      });
      const prev = blockers.map((node) => node.style.pointerEvents);
      blockers.forEach((node) => {
        node.style.pointerEvents = "none";
      });
      const row = document.elementFromPoint(x, y)?.closest(".collection-item");
      blockers.forEach((node, index) => {
        node.style.pointerEvents = prev[index] || "";
      });
      if (!row || row.dataset.collectionId === this._dragCollectionId) {
        return null;
      }
      const draggedNode = dragged || this.collectionNode(this._dragCollectionId);
      const targetNode = this.collectionNode(row.dataset.collectionId);
      if (draggedNode && targetNode && draggedNode.contains(targetNode)) {
        return null;
      }
      return row;
    },
    markCollectionNestZone(x, y, dragged) {
      this.clearCollectionDropTargets();
      this._pendingNestId = "";
      const row = this.collectionRowAtPoint(x, y, dragged);
      if (!row) {
        return false;
      }
      const rect = row.getBoundingClientRect();
      if (!rect.height) {
        return false;
      }
      const relY = (y - rect.top) / rect.height;
      if (relY < 0.16 || relY > 0.84) {
        return false;
      }
      row.classList.add("is-drop-target");
      this._pendingNestId = row.dataset.collectionId || "";
      return Boolean(this._pendingNestId);
    },
    nestCollectionInto(item, targetId) {
      if (!item || !targetId || String(targetId) === String(item.dataset.collectionId)) {
        return false;
      }
      const targetNode = this.collectionNode(targetId);
      const children = targetNode?.querySelector(":scope > .collection-children");
      if (!targetNode || !children || item.contains(targetNode)) {
        return false;
      }
      this.setCollectionExpanded(targetId, true);
      this.applyCollectionExpandState();
      children.appendChild(item);
      this.postCollectionMove(item);
      return true;
    },
    async addWorkToCollection(collectionId, uwId) {
      if (!collectionId || !uwId) {
        return;
      }
      const data = await VorApi.addWorkToCollection(
        this.collectionUrl(collectionId, "items/"),
        uwId,
      );
      if (!data?.ok) {
        return;
      }
      if (data.changed) {
        window.dispatchEvent(new Event("collection-update"));
      }
      if (this.collectionId) {
        this.reloadList();
      }
    },
    flattenCollectionTree(nodes, level = 0) {
      return window.flattenCollectionTree(nodes, level);
    },
  };
})();
