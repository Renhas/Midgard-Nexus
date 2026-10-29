document.addEventListener("alpine:init", () => {
    Alpine.store("vorArtworks", {
        deleteMode: false,
        selectedIds: [],
        workTypes: [...window.ALL_WORK_TYPES],
        showHidden: true,
        viewMode: "list",
        sortField: "custom",
        sortAsc: true,
        filters: {
            status: [],
            age_rating: [],
            tags: [],
            genre_book: [],
            genre_film: [],
            genre_game: [],
            platform: [],
        },
        filterCatalog: {
            status: [],
            age_rating: [],
            tags: [],
            genre_book: [],
            genre_film: [],
            genre_game: [],
            platform: [],
        },
        listUrl: "",
        reorderUrl: "",
        searchUrl: "",
        attachUrl: "",
        collectionTreeUrl: "",
        collectionReorderUrl: "",
        collectionId: null,
        collectionName: "",
        collectionPath: [],
        collectionDragging: false,
        isStaff: false,
        expandedCollectionIds: [],
        searchOpen: false,
        searchQuery: "",
        searchTimer: null,
        _sortable: null,
        _sortables: [],
        _collectionSortables: [],
        _artworkDragging: false,
        _collectionJustDragged: false,
        _pendingNestId: "",
        _flyoutTimer: null,
        _booted: false,
        menu: {
            open: false,
            kind: "",
            x: 0,
            y: 0,
            collectionId: null,
            collectionName: "",
            uwId: null,
            detailUrl: "",
            flyout: false,
            flyoutSide: "right",
            flyoutX: 0,
            flyoutY: 0,
            membership: [],
            membershipLoading: false,
            canNudgeUp: false,
            canNudgeDown: false,
            canLevelUp: false,
            canLevelDown: false,
            canRemoveFromCollection: false,
        },

        get listTitle() {
            return this.collectionId ? (this.collectionName || "Коллекция") : "Медиатека";
        },

        initFromPage(opts) {
            if (this._booted) {
                return;
            }
            this._booted = true;
            this.listUrl = opts.listUrl || "";
            this.reorderUrl = opts.reorderUrl || "";
            this.searchUrl = opts.searchUrl || "";
            this.attachUrl = opts.attachUrl || "";
            this.collectionTreeUrl = opts.collectionTreeUrl || "";
            this.collectionReorderUrl = opts.collectionReorderUrl || "";
            this.isStaff = Boolean(opts.isStaff);
            this.filterCatalog = { ...this.filterCatalog, ...(opts.filterCatalog || {}) };
            this.resetFilters(false);
            this.restoreSidebar();
            this.persistSidebar();
            this.applyListState();
            this.reloadList();
            this.syncCollectionSortable();
            this.applyCollectionTreeState();
        },
        restoreSidebar() {
            let saved = null;
            try {
                saved = JSON.parse(localStorage.getItem(window.SIDEBAR_STORAGE_KEY) || "null");
            } catch (error) {
                saved = null;
            }
            if (!saved) {
                return;
            }
            if (Array.isArray(saved.workTypes)) {
                this.workTypes = saved.workTypes.filter((type) => window.ALL_WORK_TYPES.includes(type));
            }
            if (typeof saved.showHidden === "boolean") {
                this.showHidden = saved.showHidden;
            }
            if (saved.viewMode === "list" || saved.viewMode === "grid") {
                this.viewMode = saved.viewMode;
            }
            if (saved.sortField) {
                this.sortField = saved.sortField;
            }
            if (typeof saved.sortAsc === "boolean") {
                this.sortAsc = saved.sortAsc;
            }
            window.FILTER_KEYS.forEach((key) => {
                this.filters[key] = window.mergeFilterSelection(
                    this.filterCatalog[key],
                    saved.filters?.[key],
                    saved.known?.[key]
                );
            });
        },
        persistSidebar() {
            const known = {};
            const filters = {};
            window.FILTER_KEYS.forEach((key) => {
                known[key] = [...(this.filterCatalog[key] || [])];
                filters[key] = [...(this.filters[key] || [])];
            });
            localStorage.setItem(window.SIDEBAR_STORAGE_KEY, JSON.stringify({
                workTypes: [...this.workTypes],
                showHidden: this.showHidden,
                viewMode: this.viewMode,
                sortField: this.sortField,
                sortAsc: this.sortAsc,
                filters,
                known,
            }));
        },
        resetFilters(reload = true) {
            window.FILTER_KEYS.forEach((key) => {
                this.filters[key] = [...(this.filterCatalog[key] || [])];
            });
            if (reload) {
                this.persistSidebar();
                this.reloadList();
            }
        },
        setShowHidden(value) {
            this.showHidden = Boolean(value);
            this.persistSidebar();
            this.reloadList();
        },
        toggleType(type) {
            const index = this.workTypes.indexOf(type);
            if (index > -1) {
                this.workTypes.splice(index, 1);
            } else {
                this.workTypes.push(type);
            }
            this.persistSidebar();
            this.reloadList();
        },
        setViewMode(mode) {
            if (this.viewMode === mode) {
                return;
            }
            this.viewMode = mode;
            this.persistSidebar();
            this.applyListState();
        },
        setSortField(field) {
            this.sortField = field;
            this.persistSidebar();
            this.applyListState();
            this.reloadList();
        },
        toggleSortDir() {
            this.sortAsc = !this.sortAsc;
            this.persistSidebar();
            this.applyListState();
            this.reloadList();
        },
        toggleFilter(name, value) {
            const list = this.filters[name] || [];
            const index = list.map(String).indexOf(String(value));
            if (index > -1) {
                list.splice(index, 1);
            } else {
                list.push(value);
            }
            this.filters[name] = list;
            this.persistSidebar();
            this.reloadList();
        },
        isFilterOn(name, value) {
            return (this.filters[name] || []).map(String).includes(String(value));
        },
        clearFilter(name) {
            this.filters[name] = [];
            this.persistSidebar();
            this.reloadList();
        },
        listQuery() {
            const params = new URLSearchParams();
            if (this.workTypes.length) {
                this.workTypes.forEach((type) => params.append("types", type));
            } else {
                params.append("types", "");
            }
            params.set("sort", this.sortField);
            params.set("dir", this.sortAsc ? "asc" : "desc");
            params.set("hidden", this.showHidden ? "1" : "0");
            if (this.collectionId) {
                params.set("collection", String(this.collectionId));
            }
            window.FILTER_KEYS.forEach((name) => {
                (this.filters[name] || []).forEach((value) => params.append(name, value));
            });
            return params;
        },
        reloadList() {
            if (!this.listUrl) {
                return;
            }
            this.closeMenu();
            htmx.ajax("GET", `${this.listUrl}?${this.listQuery().toString()}`, {
                target: "#artwork-list-body",
                swap: "innerHTML",
            });
        },
        applyListState() {
            const list = document.getElementById("artwork-list");
            if (list) {
                list.classList.toggle("is-grid", this.viewMode === "grid");
                list.classList.toggle("is-sortable", this.canDrag());
                list.classList.toggle("is-delete-mode", this.deleteMode);
            }
            this.syncSelectedDom();
            this.syncSortable();
        },
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
        canDrag() {
            return !this.deleteMode;
        },
        canReorder() {
            return this.sortField === "custom" && !this.deleteMode;
        },
        collectionUrl(id, rest = "") {
            const base = String(this.collectionTreeUrl || "").replace(/tree\/?$/, "");
            return `${base}${id}/${rest}`;
        },
        csrfHeaders() {
            return window.getCsrfHeaders();
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
            const dragViewClass = this.viewMode === "grid"
                ? "vor-artworks-grid-drag"
                : "vor-artworks-list-drag";
            const bindArtworkSortable = (container, allowSort) => {
                this._sortables.push(Sortable.create(container, {
                    group: {
                        name: "vor-artworks",
                        pull: true,
                        put: false,
                    },
                    sort: allowSort,
                    animation: 150,
                    draggable: ".artwork-item",
                    forceFallback: true,
                    fallbackOnBody: true,
                    fallbackTolerance: 4,
                    ghostClass: "is-sortable-ghost",
                    chosenClass: "is-sortable-chosen",
                    dragClass: "is-sortable-drag",
                    filter: ".artwork-row-delete, .artwork-tile-delete, .artwork-row-check, .artwork-tile-check",
                    preventOnFilter: true,
                    onStart: () => {
                        this._artworkDragging = true;
                        this.closeMenu();
                        window.getSelection?.().removeAllRanges();
                        document.body.classList.add(dragViewClass, "vor-artworks-dragging");
                    },
                    onEnd: (evt) => {
                        this._artworkDragging = false;
                        this.clearCollectionDropTargets();
                        document.body.classList.remove(
                            "vor-artworks-grid-drag",
                            "vor-artworks-list-drag",
                            "vor-artworks-dragging",
                        );
                        const point = evt.originalEvent;
                        const collectionId = this.collectionIdAtPoint(
                            point?.clientX,
                            point?.clientY,
                        );
                        if (collectionId) {
                            this.revertSortable(evt);
                            this.addWorkToCollection(collectionId, evt.item?.dataset?.uwId);
                            return;
                        }
                        const direct = document.getElementById("artwork-list-items");
                        if (
                            allowSort
                            && this.canReorder()
                            && evt.from === direct
                            && evt.to === direct
                        ) {
                            this.saveOrder();
                            return;
                        }
                        if (evt.from !== evt.to || evt.oldIndex !== evt.newIndex) {
                            this.revertSortable(evt);
                        }
                    },
                }));
            };
            const direct = document.getElementById("artwork-list-items");
            if (direct) {
                bindArtworkSortable(direct, this.canReorder());
            }
            document.querySelectorAll(".artwork-list-items-nested").forEach((container) => {
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
        saveOrder() {
            const container = document.getElementById("artwork-list-items");
            if (!container) {
                return;
            }
            const ids = [...container.querySelectorAll(":scope > .artwork-item")]
                .map((el) => el.dataset.uwId)
                .filter(Boolean);
            if (!this.sortAsc) {
                ids.reverse();
            }
            const body = new URLSearchParams();
            ids.forEach((id) => body.append("ids", id));
            const url = this.collectionId
                ? this.collectionUrl(this.collectionId, "items/reorder/")
                : this.reorderUrl;
            if (!url) {
                return;
            }
            fetch(url, {
                method: "POST",
                headers: this.csrfHeaders(),
                body,
            });
        },
        selectLibrary() {
            this.collectionId = null;
            this.collectionName = "";
            this.collectionPath = [];
            this.reloadList();
            this.applyCollectionTreeState();
        },
        collectionPathFromTree(id) {
            const item = document.querySelector(
                `.collection-item[data-collection-id="${id}"]`,
            );
            const path = [];
            let node = item?.closest(".collection-tree-node");
            while (node) {
                const row = node.querySelector(":scope > .collection-item");
                if (row?.dataset.collectionId) {
                    path.unshift({
                        id: Number(row.dataset.collectionId),
                        name: row.dataset.collectionName || "",
                    });
                }
                node = node.parentElement?.closest(".collection-tree-node") || null;
            }
            return path;
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
            return document.querySelector(`.collection-tree-node[data-collection-id="${id}"]`);
        },
        collectionSiblings(node) {
            const parent = node?.parentElement;
            if (!parent) {
                return [];
            }
            return [...parent.querySelectorAll(":scope > .collection-tree-node")];
        },
        postCollectionMove(node) {
            const parentEl = node?.parentElement;
            if (!node || !parentEl || !this.collectionReorderUrl) {
                return;
            }
            const body = new URLSearchParams();
            body.set("id", node.dataset.collectionId || "");
            body.set("parent_id", parentEl.dataset.parentId || "");
            this.collectionSiblings(node).forEach((sibling) => {
                if (sibling.dataset.collectionId) {
                    body.append("sibling_ids", sibling.dataset.collectionId);
                }
            });
            fetch(this.collectionReorderUrl, {
                method: "POST",
                headers: this.csrfHeaders(),
                body,
            }).finally(() => this.reloadCollectionTree());
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
                        this.collectionDragging = true;
                        this._pendingNestId = "";
                        this._dragCollectionId = evt.item?.dataset?.collectionId || "";
                        if (evt.item) {
                            evt.item.style.pointerEvents = "none";
                        }
                        this.closeMenu();
                        document.body.classList.add("vor-collections-dragging");
                    },
                    onEnd: (evt) => {
                        if (evt.item) {
                            evt.item.style.pointerEvents = "";
                        }
                        this.collectionDragging = false;
                        this._collectionJustDragged = true;
                        window.setTimeout(() => {
                            this._collectionJustDragged = false;
                        }, 80);
                        document.body.classList.remove("vor-collections-dragging");
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
        addWorkToCollection(collectionId, uwId) {
            if (!collectionId || !uwId) {
                return;
            }
            const body = new URLSearchParams();
            body.set("uw_id", uwId);
            body.set("action", "add");
            fetch(this.collectionUrl(collectionId, "items/"), {
                method: "POST",
                headers: this.csrfHeaders(),
                body,
            }).then((response) => response.json()).then((data) => {
                if (!data?.ok) {
                    return;
                }
                if (data.changed) {
                    window.dispatchEvent(new Event("collection-update"));
                }
                if (this.collectionId) {
                    this.reloadList();
                }
            });
        },
        placeMenu(x, y) {
            this.menu.x = x;
            this.menu.y = y;
            this.menu.open = true;
            queueMicrotask(() => {
                const el = document.getElementById("vor-context-menu");
                if (!el) {
                    return;
                }
                const rect = el.getBoundingClientRect();
                const pad = 8;
                let nextX = x;
                let nextY = y;
                if (nextX + rect.width > window.innerWidth - pad) {
                    nextX = window.innerWidth - rect.width - pad;
                }
                if (nextY + rect.height > window.innerHeight - pad) {
                    nextY = window.innerHeight - rect.height - pad;
                }
                this.menu.x = Math.max(pad, nextX);
                this.menu.y = Math.max(pad, nextY);
            });
        },
        closeMenu() {
            this.menu.open = false;
            this.menu.flyout = false;
            this.menu.membership = [];
            this.menu.canRemoveFromCollection = false;
            this.cancelCloseFlyout();
        },
        openCollectionMenu(event, el) {
            this.closeMenu();
            this.menu.kind = "collection";
            this.menu.collectionId = Number(el.dataset.collectionId);
            this.menu.collectionName = el.dataset.collectionName || "";
            const node = el.closest(".collection-tree-node");
            const siblings = this.collectionSiblings(node);
            const index = siblings.indexOf(node);
            this.menu.canNudgeUp = index > 0;
            this.menu.canNudgeDown = index >= 0 && index < siblings.length - 1;
            this.menu.canLevelUp = Boolean(node?.parentElement?.closest(".collection-tree-node"));
            this.menu.canLevelDown = index > 0;
            this.placeMenu(event.clientX, event.clientY);
        },
        openArtworkMenu(event, item) {
            if (!item || this.deleteMode) {
                return;
            }
            this.closeMenu();
            this.menu.kind = "artwork";
            this.menu.uwId = Number(item.dataset.uwId);
            this.menu.detailUrl = item.dataset.detailUrl || "";
            const nested = Boolean(item.closest(".artwork-list-items-nested"));
            const list = document.getElementById("artwork-list-items");
            const items = list
                ? [...list.querySelectorAll(":scope > .artwork-item")]
                : [];
            const index = items.indexOf(item);
            const canNudge = !nested && this.canReorder() && index >= 0;
            this.menu.canNudgeUp = canNudge && index > 0;
            this.menu.canNudgeDown = canNudge && index < items.length - 1;
            this.menu.canLevelUp = false;
            this.menu.canLevelDown = false;
            this.menu.canRemoveFromCollection = Boolean(this.collectionId) && !nested;
            this.placeMenu(event.clientX, event.clientY);
            this.loadArtworkCollections();
        },
        nudgeArtwork(delta) {
            const item = document.querySelector(
                `.artwork-item[data-uw-id="${this.menu.uwId}"]`,
            );
            const list = document.getElementById("artwork-list-items");
            this.closeMenu();
            if (!item || !list || item.closest(".artwork-list-items-nested")) {
                return;
            }
            const items = [...list.querySelectorAll(":scope > .artwork-item")];
            const index = items.indexOf(item);
            const next = index + Number(delta);
            if (index < 0 || next < 0 || next >= items.length) {
                return;
            }
            if (delta > 0) {
                items[next].after(item);
            } else {
                items[next].before(item);
            }
            this.saveOrder();
        },
        nudgeCollection(delta) {
            const node = this.collectionNode(this.menu.collectionId);
            this.closeMenu();
            if (!node) {
                return;
            }
            const siblings = this.collectionSiblings(node);
            const index = siblings.indexOf(node);
            const next = index + Number(delta);
            if (index < 0 || next < 0 || next >= siblings.length) {
                return;
            }
            if (delta > 0) {
                siblings[next].after(node);
            } else {
                siblings[next].before(node);
            }
            this.postCollectionMove(node);
        },
        shiftCollectionLevel(direction) {
            const node = this.collectionNode(this.menu.collectionId);
            this.closeMenu();
            if (!node) {
                return;
            }
            const siblings = this.collectionSiblings(node);
            const index = siblings.indexOf(node);
            if (direction > 0) {
                const prev = index > 0 ? siblings[index - 1] : null;
                const children = prev?.querySelector(":scope > .collection-children");
                if (!prev || !children) {
                    return;
                }
                this.setCollectionExpanded(prev.dataset.collectionId, true);
                children.appendChild(node);
                this.postCollectionMove(node);
                return;
            }
            const parentNode = node.parentElement?.closest(".collection-tree-node");
            if (!parentNode) {
                return;
            }
            parentNode.after(node);
            this.postCollectionMove(node);
        },
        flattenCollectionTree(nodes, level = 0) {
            const out = [];
            (nodes || []).forEach((node) => {
                out.push({
                    id: node.id,
                    name: node.name,
                    in_collection: Boolean(node.in_collection),
                    level,
                });
                if (node.children?.length) {
                    out.push(...this.flattenCollectionTree(node.children, level + 1));
                }
            });
            return out;
        },
        loadArtworkCollections() {
            if (!this.menu.uwId || !this.listUrl) {
                return;
            }
            this.menu.membershipLoading = true;
            fetch(`${this.listUrl}${this.menu.uwId}/collections/`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            }).then((response) => response.json()).then((data) => {
                this.menu.membership = this.flattenCollectionTree(data.tree || []);
                this.menu.membershipLoading = false;
            }).catch(() => {
                this.menu.membershipLoading = false;
            });
        },
        openCollectionFlyout() {
            this.cancelCloseFlyout();
            this.menu.flyout = true;
            const menu = document.getElementById("vor-context-menu");
            const trigger = menu?.querySelector(".has-submenu");
            const rect = (trigger || menu)?.getBoundingClientRect();
            if (!rect) {
                return;
            }
            const width = 220;
            const spaceRight = window.innerWidth - rect.right;
            this.menu.flyoutSide = spaceRight > width ? "right" : "left";
            this.menu.flyoutX = spaceRight > width ? rect.right : rect.left - width;
            this.menu.flyoutY = rect.top;
        },
        toggleCollectionFlyout() {
            if (this.menu.flyout) {
                this.menu.flyout = false;
                return;
            }
            this.openCollectionFlyout();
        },
        scheduleCloseFlyout() {
            this.cancelCloseFlyout();
            this._flyoutTimer = window.setTimeout(() => {
                this.menu.flyout = false;
            }, 180);
        },
        cancelCloseFlyout() {
            if (this._flyoutTimer) {
                window.clearTimeout(this._flyoutTimer);
                this._flyoutTimer = null;
            }
        },
        removeFromCurrentCollection() {
            const collectionId = this.collectionId;
            const uwId = this.menu.uwId;
            this.closeMenu();
            if (!collectionId || !uwId) {
                return;
            }
            const body = new URLSearchParams();
            body.set("uw_id", String(uwId));
            body.set("action", "remove");
            fetch(this.collectionUrl(collectionId, "items/"), {
                method: "POST",
                headers: this.csrfHeaders(),
                body,
            }).then((response) => response.json()).then((data) => {
                if (!data?.ok) {
                    return;
                }
                window.dispatchEvent(new Event("collection-update"));
                this.reloadList();
            });
        },
        toggleWorkCollection(item) {
            if (!item || !this.menu.uwId) {
                return;
            }
            const adding = !item.in_collection;
            const body = new URLSearchParams();
            body.set("uw_id", String(this.menu.uwId));
            body.set("action", adding ? "add" : "remove");
            fetch(this.collectionUrl(item.id, "items/"), {
                method: "POST",
                headers: this.csrfHeaders(),
                body,
            }).then((response) => response.json()).then((data) => {
                if (!data?.ok) {
                    return;
                }
                item.in_collection = adding;
                window.dispatchEvent(new Event("collection-update"));
                this.reloadList();
            });
        },
        menuRenameCollection() {
            const id = this.menu.collectionId;
            this.closeMenu();
            if (!id) {
                return;
            }
            htmx.ajax("GET", this.collectionUrl(id, "edit/"), {
                target: "#vor-modal",
                swap: "innerHTML",
            });
        },
        menuDeleteCollection() {
            const id = this.menu.collectionId;
            this.closeMenu();
            if (!id) {
                return;
            }
            htmx.ajax("GET", this.collectionUrl(id, "delete/preview/"), {
                target: "#vor-modal",
                swap: "innerHTML",
            });
        },
        menuEditArtwork() {
            let url = this.menu.detailUrl;
            this.closeMenu();
            if (!url) {
                return;
            }
            if (this.isStaff) {
                url += (url.includes("?") ? "&" : "?") + "edit=1";
            }
            htmx.ajax("GET", url, {
                target: "#vor-overlay",
                swap: "innerHTML",
            });
        },
        menuDeleteArtwork() {
            const id = this.menu.uwId;
            const base = document.getElementById("vor-modal")?.dataset.vorDeletePreview;
            this.closeMenu();
            if (!id || !base) {
                return;
            }
            htmx.ajax("GET", `${base}?ids=${id}`, {
                target: "#vor-modal",
                swap: "innerHTML",
            });
        },
        onCollectionDeleted(id) {
            if (String(this.collectionId) === String(id)) {
                this.selectLibrary();
            }
        },
        openSearch() {
            if (this.searchOpen) {
                document.getElementById("vor-library-search-input")?.focus();
                return;
            }
            this.searchOpen = true;
            window.syncPageScrollLock();
            this.searchQuery = "";
            const results = document.getElementById("vor-library-search-results");
            if (results) {
                results.innerHTML = "";
            }
            queueMicrotask(() => document.getElementById("vor-library-search-input")?.focus());
        },
        closeSearch() {
            this.searchOpen = false;
            window.syncPageScrollLock();
            this.searchQuery = "";
            const results = document.getElementById("vor-library-search-results");
            if (results) {
                results.innerHTML = "";
            }
        },
        onSearchInput() {
            clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(() => this.runSearch(), 280);
        },
        runSearch() {
            const query = String(this.searchQuery || "").trim();
            const results = document.getElementById("vor-library-search-results");
            if (!query || !this.searchUrl) {
                if (results) {
                    results.innerHTML = "";
                }
                return;
            }
            htmx.ajax("GET", `${this.searchUrl}?q=${encodeURIComponent(query)}`, {
                target: "#vor-library-search-results",
                swap: "innerHTML",
            });
        },
        attachFromSearch(typeKey, workId) {
            const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value
                || window.getCookie("csrftoken");
            const body = new URLSearchParams({
                work_type: typeKey,
                work_id: String(workId),
                status: "planning",
            });
            fetch(this.attachUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": token || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
                body,
            })
                .then((response) => (response.ok ? response.json() : null))
                .then((data) => {
                    if (!data?.ok) {
                        return;
                    }
                    this.reloadList();
                    this.runSearch();
                });
        },
        openWork(url) {
            this.closeSearch();
            htmx.ajax("GET", url, {
                target: "#vor-overlay",
                swap: "innerHTML",
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
        closeOverlay() {
            if (this._closingOverlay) {
                return;
            }
            const data = window.overlayAlpine();
            if (data?.editing && data.dirtyChanges().length) {
                data.tryLeave(() => this.closeOverlay());
                return;
            }
            this._closingOverlay = true;
            queueMicrotask(() => {
                this._closingOverlay = false;
            });
            if (history.state && history.state.vorOverlay) {
                history.back();
                return;
            }
            const el = document.getElementById("vor-overlay");
            if (el) {
                el.innerHTML = "";
            }
        },
        closeModal() {
            const el = document.getElementById("vor-modal");
            if (el) {
                el.innerHTML = "";
            }
        },
    });
});
