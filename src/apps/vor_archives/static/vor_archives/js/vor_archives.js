(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function hasContent(id) {
        const el = document.getElementById(id);
        return Boolean(el && el.innerHTML.trim());
    }

    function syncPageScrollLock() {
        const locked = hasContent("vor-overlay")
            || Boolean(window.Alpine?.store("vorArtworks")?.searchOpen);
        document.documentElement.classList.toggle("vor-scroll-lock", locked);
    }

    function overlayAlpine() {
        const el = document.querySelector("#vor-overlay .vor-overlay");
        return el && window.Alpine ? Alpine.$data(el) : null;
    }

    function cropCoverFile(file) {
        const targetRatio = 2 / 3;
        return new Promise((resolve, reject) => {
            const image = new Image();
            const url = URL.createObjectURL(file);
            image.onload = () => {
                URL.revokeObjectURL(url);
                const srcW = image.naturalWidth;
                const srcH = image.naturalHeight;
                const srcRatio = srcW / srcH;
                if (Math.abs(srcRatio - targetRatio) < 0.01) {
                    resolve({ file, cropped: false, srcW, srcH, outW: srcW, outH: srcH });
                    return;
                }
                let sx = 0;
                let sy = 0;
                let sw = srcW;
                let sh = srcH;
                if (srcRatio > targetRatio) {
                    sw = srcH * targetRatio;
                    sx = (srcW - sw) / 2;
                } else {
                    sh = srcW / targetRatio;
                    sy = (srcH - sh) / 2;
                }
                const canvas = document.createElement("canvas");
                canvas.width = Math.max(1, Math.round(sw));
                canvas.height = Math.max(1, Math.round(sh));
                canvas.getContext("2d").drawImage(
                    image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height
                );
                canvas.toBlob((blob) => {
                    if (!blob) {
                        reject(new Error("cover"));
                        return;
                    }
                    const next = new File([blob], file.name.replace(/\.\w+$/, ".jpg"), {
                        type: "image/jpeg",
                    });
                    resolve({
                        file: next,
                        cropped: true,
                        srcW,
                        srcH,
                        outW: canvas.width,
                        outH: canvas.height,
                    });
                }, "image/jpeg", 0.92);
            };
            image.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error("cover"));
            };
            image.src = url;
        });
    }

    const DATE_MONTHS_FULL = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ];
    const DATE_MONTHS_SHORT = [
        "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
        "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек",
    ];

    function toIsoDate(date) {
        return [
            date.getFullYear(),
            String(date.getMonth() + 1).padStart(2, "0"),
            String(date.getDate()).padStart(2, "0"),
        ].join("-");
    }

    function wheelDirection(event) {
        return event.deltaY < 0 ? 1 : event.deltaY > 0 ? -1 : 0;
    }

    function datePickerApi() {
        return {
            dateView: "days",
            formatDate(iso) {
                if (!iso) {
                    return "";
                }
                const [year, month, day] = iso.split("-");
                return `${day}.${month}.${year}`;
            },
            dateCursorDate() {
                return this.dateCursor || new Date();
            },
            dateMonthLabel() {
                const cursor = this.dateCursorDate();
                return `${DATE_MONTHS_FULL[cursor.getMonth()]} ${cursor.getFullYear()}`;
            },
            dateHeaderLabel() {
                if (this.dateView === "years") {
                    const start = this.yearGridStart();
                    return `${start}–${start + 11}`;
                }
                if (this.dateView === "months") {
                    return String(this.dateCursorDate().getFullYear());
                }
                return this.dateMonthLabel();
            },
            toggleDateOpen() {
                this.dateOpen = !this.dateOpen;
                if (this.dateOpen) {
                    this.dateView = "days";
                }
            },
            closeDatePopup() {
                this.dateOpen = false;
                this.dateView = "days";
            },
            onDateHeaderClick() {
                if (this.dateView === "days") {
                    this.dateView = "months";
                    return;
                }
                if (this.dateView === "months") {
                    this.dateView = "years";
                }
            },
            shiftDateNav(delta) {
                const cursor = new Date(this.dateCursorDate());
                if (this.dateView === "years") {
                    cursor.setFullYear(cursor.getFullYear() + delta * 12);
                } else if (this.dateView === "months") {
                    cursor.setFullYear(cursor.getFullYear() + delta);
                } else {
                    cursor.setMonth(cursor.getMonth() + delta);
                }
                this.dateCursor = cursor;
            },
            shiftMonth(delta) {
                this.shiftDateNav(delta);
            },
            dateCells() {
                const cursor = this.dateCursorDate();
                const year = cursor.getFullYear();
                const month = cursor.getMonth();
                const first = new Date(year, month, 1);
                const startOffset = (first.getDay() + 6) % 7;
                const start = new Date(year, month, 1 - startOffset);
                const cells = [];
                for (let index = 0; index < 42; index += 1) {
                    const date = new Date(start);
                    date.setDate(start.getDate() + index);
                    const iso = toIsoDate(date);
                    cells.push({
                        key: iso + index,
                        iso,
                        day: date.getDate(),
                        current: date.getMonth() === month,
                    });
                }
                return cells;
            },
            monthCells() {
                return DATE_MONTHS_SHORT;
            },
            yearGridStart() {
                const year = this.dateCursorDate().getFullYear();
                return year - (year % 12);
            },
            yearCells() {
                const start = this.yearGridStart();
                return Array.from({ length: 12 }, (_, index) => start + index);
            },
            isMonthSelected(index) {
                return this.dateCursorDate().getMonth() === index;
            },
            isYearSelected(year) {
                return this.dateCursorDate().getFullYear() === year;
            },
            selectMonth(index) {
                const cursor = new Date(this.dateCursorDate());
                cursor.setMonth(index);
                this.dateCursor = cursor;
                this.dateView = "days";
            },
            selectYear(year) {
                const cursor = new Date(this.dateCursorDate());
                cursor.setFullYear(year);
                this.dateCursor = cursor;
                this.dateView = "months";
            },
            setReleaseDate(iso) {
                this.releaseDate = iso;
                this.dateOpen = false;
                this.dateView = "days";
                if (iso) {
                    this.dateCursor = new Date(`${iso}T00:00:00`);
                }
            },
            setTodayDate() {
                this.setReleaseDate(toIsoDate(new Date()));
            },
            onNumberWheel(event, field, min = 1, max = null) {
                const direction = wheelDirection(event);
                if (!direction) {
                    return;
                }
                const raw = this[field];
                const value = raw === "" || raw == null ? 0 : Number(raw);
                const current = Number.isFinite(value) ? value : 0;
                let next = current + direction;
                if (next < min) {
                    next = current === 0 && direction < 0 ? 0 : min;
                }
                if (max != null && next > max) {
                    next = max;
                }
                this[field] = next < min ? "" : next;
            },
            onAgeWheel(event) {
                const direction = wheelDirection(event);
                if (!direction) {
                    return;
                }
                const options = [""].concat((this.ageChoices || []).map((item) => item.value));
                const index = Math.max(0, options.indexOf(this.ageRating || ""));
                const next = Math.max(0, Math.min(options.length - 1, index + direction));
                this.ageRating = options[next];
            },
            onFilmTypeWheel(event) {
                const direction = wheelDirection(event);
                if (!direction) {
                    return;
                }
                const options = ["movie", "tv_show"];
                const index = Math.max(0, options.indexOf(this.filmType || "movie"));
                const next = Math.max(0, Math.min(options.length - 1, index + direction));
                this.filmType = options[next];
            },
        };
    }

    function overlayRequestPath(event) {
        const raw =
            event.detail.pathInfo?.requestPath ||
            event.detail.xhr?.responseURL ||
            "";
        try {
            const url = new URL(raw, window.location.origin);
            return url.pathname + url.search;
        } catch (error) {
            return raw;
        }
    }

    function pushOverlayHistory(event) {
        if (window.__vorRestoringOverlay) {
            window.__vorRestoringOverlay = false;
            return;
        }
        if (!hasContent("vor-overlay")) {
            return;
        }
        const overlayUrl = overlayRequestPath(event);
        if (!overlayUrl || history.state?.vorOverlay === overlayUrl) {
            return;
        }
        history.pushState({ vorOverlay: overlayUrl }, "", window.location.href);
    }

    function restoreOverlay(overlayUrl) {
        window.__vorRestoringOverlay = true;
        htmx.ajax("GET", overlayUrl, {
            target: "#vor-overlay",
            swap: "innerHTML",
        });
    }

    function leaveOverlayOnCurrentPage() {
        if (!hasContent("vor-overlay")) {
            return false;
        }
        const proceed = () => {
            if (history.state?.vorOverlay) {
                history.pushState({}, "", window.location.href);
            }
            const el = document.getElementById("vor-overlay");
            if (el) {
                el.innerHTML = "";
            }
        };
        const data = overlayAlpine();
        if (data?.editing) {
            return data.tryLeave(proceed);
        }
        proceed();
        return true;
    }

    function isSamePageLink(anchor) {
        if (!anchor?.href || anchor.target && anchor.target !== "_self") {
            return false;
        }
        try {
            const url = new URL(anchor.href, window.location.origin);
            return (
                url.origin === window.location.origin &&
                url.pathname === window.location.pathname &&
                url.search === window.location.search
            );
        } catch (error) {
            return false;
        }
    }

    window.addEventListener("popstate", (event) => {
        const overlayUrl = event.state && event.state.vorOverlay;
        if (overlayUrl) {
            restoreOverlay(overlayUrl);
            return;
        }
        const el = document.getElementById("vor-overlay");
        if (el) {
            el.innerHTML = "";
        }
    });

    document.addEventListener(
        "click",
        (event) => {
            if (event.defaultPrevented || event.button !== 0) {
                return;
            }
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
                return;
            }
            const anchor = event.target.closest("a[href]");
            if (!anchor || !hasContent("vor-overlay")) {
                return;
            }
            if (isSamePageLink(anchor)) {
                event.preventDefault();
                leaveOverlayOnCurrentPage();
                return;
            }
            const data = overlayAlpine();
            if (!data?.editing || !data.dirtyChanges().length) {
                return;
            }
            event.preventDefault();
            data.tryLeave(() => {
                window.location.href = anchor.href;
            });
        },
        true
    );

    document.body.addEventListener("htmx:configRequest", (event) => {
        const token =
            document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
            getCookie("csrftoken");
        if (token) {
            event.detail.headers["X-CSRFToken"] = token;
        }
    });

    const SIDEBAR_STORAGE_KEY = "vor.artworks.sidebar";
    const ALL_WORK_TYPES = ["book", "film", "game"];
    const FILTER_KEYS = [
        "status", "age_rating", "tags", "genre_book", "genre_film", "genre_game", "platform",
    ];

    function mergeFilterSelection(allIds, savedSelected, savedKnown) {
        const catalog = allIds || [];
        if (!savedSelected && !savedKnown) {
            return [...catalog];
        }
        const selected = new Set((savedSelected || []).map(String));
        const known = new Set((savedKnown || []).map(String));
        return catalog.filter((id) => {
            const key = String(id);
            return !known.has(key) || selected.has(key);
        });
    }

    document.body.addEventListener("htmx:afterSwap", (event) => {
        const el = event.detail.elt;
        if (el?.id === "vor-overlay") {
            pushOverlayHistory(event);
        }
        if (el?.id === "vor-library-search-results") {
            window.Alpine?.initTree?.(el);
        }
        if (el?.id === "artwork-list-body" || el?.id === "artwork-list") {
            window.Alpine?.initTree?.(el);
            window.Alpine?.store("vorArtworks")?.applyListState();
        }
        if (el?.id === "sidebar-collections-list") {
            window.Alpine?.destroyTree?.(el);
            window.Alpine?.initTree?.(el);
            const store = window.Alpine?.store("vorArtworks");
            store?.pruneExpandedCollections();
            store?.applyCollectionTreeState();
            store?.syncCollectionSortable();
            store?.refreshCollectionPath();
        }
        if (el?.id === "vor-modal") {
            window.Alpine?.initTree?.(el);
        }
        if (el?.id === "dash-heatmap" || el?.id === "dash-feed-more") {
            window.Alpine?.initTree?.(el);
        }
        syncPageScrollLock();
    });

    const overlayEl = document.getElementById("vor-overlay");
    if (overlayEl) {
        new MutationObserver(syncPageScrollLock).observe(overlayEl, { childList: true });
    }

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
        window.Alpine?.store("vorArtworks")?.openSearch();
    }, true);

    document.addEventListener("alpine:init", () => {
        Alpine.store("vorArtworks", {
            deleteMode: false,
            selectedIds: [],
            workTypes: [...ALL_WORK_TYPES],
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
                    saved = JSON.parse(localStorage.getItem(SIDEBAR_STORAGE_KEY) || "null");
                } catch (error) {
                    saved = null;
                }
                if (!saved) {
                    return;
                }
                if (Array.isArray(saved.workTypes)) {
                    this.workTypes = saved.workTypes.filter((type) => ALL_WORK_TYPES.includes(type));
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
                FILTER_KEYS.forEach((key) => {
                    this.filters[key] = mergeFilterSelection(
                        this.filterCatalog[key],
                        saved.filters?.[key],
                        saved.known?.[key]
                    );
                });
            },
            persistSidebar() {
                const known = {};
                const filters = {};
                FILTER_KEYS.forEach((key) => {
                    known[key] = [...(this.filterCatalog[key] || [])];
                    filters[key] = [...(this.filters[key] || [])];
                });
                localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify({
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
                FILTER_KEYS.forEach((key) => {
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
                FILTER_KEYS.forEach((name) => {
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
                const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value
                    || getCookie("csrftoken");
                return {
                    "X-CSRFToken": token || "",
                    "X-Requested-With": "XMLHttpRequest",
                };
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
                syncPageScrollLock();
                this.searchQuery = "";
                const results = document.getElementById("vor-library-search-results");
                if (results) {
                    results.innerHTML = "";
                }
                queueMicrotask(() => document.getElementById("vor-library-search-input")?.focus());
            },
            closeSearch() {
                this.searchOpen = false;
                syncPageScrollLock();
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
                    || getCookie("csrftoken");
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
                const data = overlayAlpine();
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
        const DASH_CHART_COLORS = [
            "#A78BFA", "#60A5FA", "#34D399", "#F87171", "#FB923C",
            "#818CF8", "#FBBF24", "#22D3EE", "#F472B6", "#94A3B8",
            "#C084FC", "#38BDF8",
        ];

        const MIN_SIZE_PX = 12;
        const MAX_SIZE_PX = 48;

        const centerTextPlugin = {
            id: "centerText",
            afterDraw(chart, args, opts) {
                if (!opts?.text) return;
                const { ctx, chartArea } = chart;
                if (!chartArea) return;
                const cx = (chartArea.left + chartArea.right) / 2;
                const cy = (chartArea.top + chartArea.bottom) / 2;
                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.font = "bold 28px sans-serif";
                ctx.fillStyle = "#E2E8F0";
                ctx.fillText(opts.text, cx, cy - 8);
                if (opts.label) {
                    ctx.font = "12px sans-serif";
                    ctx.fillStyle = "#94A3B8";
                    ctx.fillText(opts.label, cx, cy + 16);
                }
                ctx.restore();
            },
        };

        function readJsonScript(id) {
            const el = document.getElementById(id);
            if (!el) {
                return {};
            }
            try {
                return JSON.parse(el.textContent);
            } catch (error) {
                return {};
            }
        }

        function formatDashPercent(value) {
            const number = Number(value || 0);
            if (!number) {
                return "0%";
            }
            if (Number.isInteger(number)) {
                return `${number}%`;
            }
            return `${number}%`;
        }

        Alpine.data("vorDashStats", () => ({
            workTypes: ["book", "film", "game"],
            pieCharts: { types: null, statuses: null , age: null, rating: null},
            barCharts: { rating: null},
            statusMatrix: {},
            ageMatrix: {},
            ratingMatrix: {},
            spent: {},
            typeMeta: {},
            statusChoices: {},
            ageChoices: {},
            ratingChoices: {},

            init() {
                const data = readJsonScript("dash-stats-opts");
                this.statusMatrix = data.status_matrix || {};
                this.ageMatrix = data.age_matrix || {};
                this.ratingMatrix = data.rating_matrix || {};
                this.spent = data.spent || {};
                this.typeMeta = data.type_meta || {};
                this.statusChoices = data.status_choices || {}
                this.ageChoices = data.age_choices || {};
                this.ratingChoices = data.rating_choices || {};

                console.log("[charts] init, raw data:", data);
                console.log("[charts] typeMeta:", this.typeMeta);
                this.$nextTick(() => {
                    this.renderPieTypes();
                    this.renderPieStatus();
                    this.renderPieAge();
                    this.renderPieRating();
                    this.renderBarRating();
                });

                this.$watch("pieStatusItems", () => {
                    this.$nextTick(() => this.renderPieStatus());
                });
                this.$watch("pieAgeItems", () => {
                    this.$nextTick(() => this.renderPieAge());
                });
                this.$watch("pieRatingItems", () => {
                    this.$nextTick(() => this.renderPieRating());
                });
            },
            get worksTotalCount() {
                return Object.keys(this.typeMeta).reduce((sum, type) => sum + this.sumByRow(type, this.statusMatrix), 0);
            },
            get averageRating() {
                if (!this.workTypes.length) return "0.0";
                const total_res = this.workTypes.reduce((res, type) => {
                    const row_res = this.sumByRowWithCount(type, this.ratingMatrix);
                    res.sum += row_res.sum;
                    res.count += row_res.count;
                    return res;
                }, {"sum": 0, "count": 0});
                return total_res.count ? (total_res.sum / total_res.count).toFixed(1) : "0.0";
            },
            get spentProgressItems() {
                return Object.entries(this.spent).map(([key, value]) => ({
                    key: key,
                    count: value,
                    unit: this.typeMeta[key].unit,
                    icon: this.typeMeta[key].icon,
                }));
            },
            get pieTypesItems() {
                return Object.keys(this.typeMeta).map(type => ({
                    label: this.typeMeta[type].label,
                    count: this.sumByRow(type, this.statusMatrix),
                }));
            },
            get pieStatusItems() {
                if (!this.workTypes.length) return {};
                return Object.keys(this.statusChoices).map(status => ({
                    label: this.statusChoices[status].label,
                    count: this.sumByCol(status, this.statusMatrix),
                }));
            },
            get pieAgeItems() {
                if (!this.workTypes.length) return {};
                return Object.keys(this.ageChoices).map(age => ({
                    label: this.ageChoices[age].label,
                    count: this.sumByCol(age, this.ageMatrix),
                }));
            },
            get pieRatingItems() {
                if (!this.workTypes.length) return {};
                return Object.keys(this.ratingChoices).map(age => ({
                    label: this.ratingChoices[age].label,
                    count: this.sumByCol(age, this.ratingMatrix),
                }));
            },
            get barRatingItems() {
                return Object.keys(this.typeMeta).map(type => {
                    const { sum, count } = this.sumByRowWithCount(type, this.ratingMatrix);
                    return {
                    label: this.typeMeta[type].label,
                    count: this.avgStr(sum, count)};
                });
            },
            toggleType(type) {
                const index = this.workTypes.indexOf(type);
                if (index > -1) {
                    this.workTypes.splice(index, 1);
                } else {
                    this.workTypes.push(type);
                }
            },
            sumByCol(col, matrix) {
                return this.workTypes.reduce((sum, type) =>
                    sum + (matrix[type]?.[col] || 0), 0);
            },
            sumByRow(row, matrix) {
                const row_data = matrix[row] || {};
                return Object.values(row_data).reduce((sum, val) => sum + val, 0)
            },
            sumByRowWithCount(row, matrix) {
                const row_data = matrix[row] || {};
                return Object.entries(row_data).reduce((res, [rating, count]) => {
                        if (rating === "") return res;
                        res.sum += Number(rating) * count;
                        res.count += count;
                        return res;
                }, {"sum": 0, "count": 0});
            },
            avgStr(sum, count) {
                return count ? (sum / count).toFixed(1) : "0.0";
            },
            formatNumber(number) {
                console.log("[charts] number:", Number(number));
                return Number(number).toFixed(1).toLocaleString("ru-RU");
            },
            _renderPie(key, canvas, items, { centerText = null } = {}) {
                console.log(`[charts] _renderPie key=${key}`, {
                    canvas: !!canvas,
                    existing: canvas ? !!Chart.getChart(canvas) : null,
                    stored: !!this.pieCharts[key],
                });
                if (!canvas || !window.Chart) return;
                Chart.getChart(canvas)?.destroy();
                this.pieCharts[key] = null;
                if (!items.length) return;

                this.pieCharts[key] = new Chart(canvas, {
                    type: "doughnut",
                    data: {
                        labels: items.map(i => i.label),
                        datasets: [{
                            data: items.map(i => i.count),
                            backgroundColor: items.map(
                                (_, index) => DASH_CHART_COLORS[index % DASH_CHART_COLORS.length]
                            ),
                            borderColor: "#1A233A",
                            borderWidth: 2,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: "bottom",
                                labels: {
                                    boxWidth: 12,
                                    color: "#E2E8F0",
                                },
                            },
                            centerText: centerText
                                ? {"text": centerText.value, "label": centerText.label, }
                                : undefined,
                        },
                    },
                    plugins: [centerTextPlugin]
                });
            },
            _renderBar(key, canvas, items) {
                console.log(`[charts] _renderBar key=${key}`, {
                    canvas: !!canvas,
                    existing: canvas ? !!Chart.getChart(canvas) : null,
                    stored: !!this.barCharts[key],
                });
                if (!canvas || !window.Chart) return;
                Chart.getChart(canvas)?.destroy();
                this.barCharts[key] = null;
                if (!items.length) return;

                this.barCharts[key] = new Chart(canvas, {
                    type: "bar",
                    data: {
                        labels: items.map(i => i.label),
                        datasets: [{
                            data: items.map(i => i.count),
                            backgroundColor: items.map(
                                (_, index) => DASH_CHART_COLORS[index % DASH_CHART_COLORS.length]
                            ),
                            borderRadius: 4,
                            borderSkipped: false,
                            barThickness: "flex",
                            maxBarThickness: 96,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                suggestedMax: 10,
                                ticks: {
                                    color: "#94A3B8",
                                    font: { size: 11 },
                                    precision: 0,     // целые числа на оси
                                },
                                grid: { color: "rgba(255,255,255,0.06)" },
                                border: { display: false },
                            },
                            x: {
                                ticks: {
                                    color: "#94A3B8",
                                    font: { size: 11 },
                                },
                                grid: { display: false },
                                border: { display: false },
                            },
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: "#1A233A",
                                titleColor: "#E2E8F0",
                                bodyColor: "#E2E8F0",
                                borderColor: "rgba(167,139,250,0.3)",
                                borderWidth: 1,
                            },
                        },
                    }
                });
            },
            renderPieTypes() {
                this._renderPie(
                    "types",
                    this.$refs.pieTypes,
                    this.pieTypesItems,
                    { centerText: { value: this.worksTotalCount, label: "всего" } }
                );
            },
            renderPieStatus() {
                this._renderPie(
                    "statuses",
                    this.$refs.pieStatus,
                    this.pieStatusItems,
                    { centerText: null }
                );
            },
            renderPieAge() {
                this._renderPie(
                    "age",
                    this.$refs.pieAge,
                    this.pieAgeItems,
                    { centerText: null }
                );
            },
            renderPieRating() {
                this._renderPie(
                    "rating",
                    this.$refs.pieRating,
                    this.pieRatingItems,
                    { centerText: { value: this.averageRating, label: "среднее"} }
                );
            },
            renderBarRating() {
                this._renderBar(
                    "rating",
                    this.$refs.barRating,
                    this.barRatingItems,
                );
            },
        }));

        Alpine.data("vorDashAttrs", () => {
            const barCharts = Object.create(null);
            const cloudCharts = Object.create(null);
            return {
                attrView: "cloud",
                attrs: {},
                attrTotals: {},
                totalWorks: 0,
                histTopN: 12,
                init() {
                    const data = readJsonScript("dash-attrs-opts");
                    this.attrs = data.attrs || {};
                    this.totalWorks = data.total;
                    this.histTopN = data.histTopN || 12;
                    this.calcAttrTotal();
                    console.log("[attrs] raw input data", data);
                    console.log("[attrs] attrView", this.attrView);
                    console.log("[attrs] attrs", this.attrs);
                    console.log("[attrs] attrTotals", this.attrTotals);
                    this.$nextTick(() => this._updateData());
                    this.$watch("attrView", () => this._updateData());
                    this.$watch("attrs", () => this._updateData());
                },
                calcAttrTotal() {
                    this.attrTotals = Object.fromEntries(
                        Object.entries(this.attrs).map(([key, items]) => [
                            key,
                            items.reduce((sum, item) => sum + (item.count || 0), 0),
                        ])
                    );
                },
                getItems(attrKey) {
                    return this.attrs[attrKey];
                },
                getHistItems(attrKey) {
                    return this.attrs[attrKey].slice(0, this.histTopN).map((item) => ({
                        label: item.name,
                        count: item.count,
                    }));
                },
                getCloudItems(attrKey) {
                    const items = this.attrs[attrKey];
                    if (!items.length) return [];

                    const counts = items.map(i => i.count);
                    const min = Math.min(...counts);
                    const max = Math.max(...counts);

                    return items.map(item => {
                        const size = min === max ? (MIN_SIZE_PX + MAX_SIZE_PX) / 2
                            : MIN_SIZE_PX + ((item.count - min) / (max - min)) * (MAX_SIZE_PX - MIN_SIZE_PX);

                        return {
                            label: item.name,
                            count: item.count,
                            size,
                        };
                    });
                },
                calcAttrShare(count, attrKey) {
                    const total = this.attrTotals[attrKey];
                    return total ? (count / total).toFixed(1) : 0;
                },
                formatPercent: formatDashPercent,
                setAttrView(view) {
                    if (view === this.attrView) return;
                    this.attrView = view;
                },
                _updateData() {
                    console.log("[attrs | _updateData] view", this.attrView);
                    if (this.attrView === "bar") {
                        this.$nextTick(() => this._renderAllBars());
                    }
                    if (this.attrView === "cloud") {
                        this.$nextTick(() => this._renderAllClouds());
                    }
                },
                _deleteAllBars() {
                    for (const key of Object.keys(barCharts)) {
                        try {
                            barCharts[key]?.stop();
                            barCharts[key]?.destroy();
                        } catch (e) {
                            console.error('[attrs] destroy failed for', key, e);
                        }
                        delete barCharts[key];
                    }
                },
                _deleteAllClouds() {
                    for (const key of Object.keys(cloudCharts)) {
                        try {
                            cloudCharts[key]?.stop();
                            cloudCharts[key]?.destroy();
                        } catch (e) {
                            console.error('[attrs] destroy failed for', key, e);
                        }
                        delete cloudCharts[key];
                    }
                },
                _renderAllBars() {
                    console.log("[attrs | _renderAllBars] Start render");
                    Object.keys(this.attrs).forEach((key) => this.renderSingleBar(key));
                    console.log("[attrs | _renderAllBars] End render");
                },
                _renderAllClouds() {
                    console.log("[attrs | _renderAllClouds] Start render");
                    Object.keys(this.attrs).forEach((key) => this.renderSingleCloud(key));
                    console.log("[attrs | _renderAllClouds] End render");
                },
                _formBarData(items) {
                    return {
                        labels: items.map(i => i.label),
                        data: items.map(i => i.count),
                        bgColor: items.map(
                            (_, index) => DASH_CHART_COLORS[index % DASH_CHART_COLORS.length]
                        ),
                    }
                },
                _formCloudData(items) {
                    return {
                        labels: items.map(i => i.label),
                        data: items.map(i => i.size),
                        counts: items.map(i => i.count),
                        color: DASH_CHART_COLORS[0],
                    }
                },
                _renderBar(key, canvas, items) {
                    console.log(`[attrs | _renderBar] _renderBar key=${key}`, {
                        canvas: !!canvas,
                        existing: canvas ? !!Chart.getChart(canvas) : null,
                        stored: !!barCharts[key],
                        items: items,
                    });
                    if (!canvas || !window.Chart) return;
                    const { labels, data, bgColor } = this._formBarData(items);
                    if (barCharts[key]) {
                        const chart = barCharts[key];
                        console.log(`[attrs | _renderBar] _renderBar key=${key}`, `Work with chart=${chart}`);
                        chart.data.labels = labels;
                        chart.data.datasets[0].data = data;
                        chart.data.datasets[0].backgroundColor = bgColor;
                        console.log(`[attrs | _renderBar] _renderBar key=${key}`, "Data Updated with", {
                            labels: labels,
                            data: data,
                            bgColor: bgColor,
                        });
                        chart.update();
                        console.log(`[attrs | _renderBar] _renderBar key=${key}`, "Updated!");
                        return;
                    }

                    barCharts[key] = new Chart(canvas, {
                        type: "bar",
                        data: {
                            labels: labels,
                            datasets: [{
                                data: data,
                                backgroundColor: bgColor,
                                borderRadius: 4,
                                borderSkipped: false,
                                barThickness: "flex",
                                maxBarThickness: 96,
                            }],
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        color: "#94A3B8",
                                        font: { size: 11 },
                                    },
                                    grid: { display: false },
                                    border: { display: false },
                                },
                                x: {
                                    ticks: {
                                        color: "#94A3B8",
                                        font: { size: 11 },
                                        precision: 0,
                                    },
                                    grid: { color: "rgba(255,255,255,0.06)" },
                                    border: { display: false },
                                },
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: "#1A233A",
                                    titleColor: "#E2E8F0",
                                    bodyColor: "#E2E8F0",
                                    borderColor: "rgba(167,139,250,0.3)",
                                    borderWidth: 1,
                                },
                            },
                        }
                    });
                },
                _renderCloud(key, canvas, items) {
                    console.log(`[attrs | _renderCloud] _renderCloud key=${key}`, {
                        canvas: !!canvas,
                        existing: canvas ? !!Chart.getChart(canvas) : null,
                        stored: !!cloudCharts[key],
                        items: items,
                    });
                    if (!canvas || !window.Chart) return;
                    const { labels, data, counts, color } = this._formCloudData(items);
                    if (cloudCharts[key]) {
                        const chart = cloudCharts[key];
                        console.log(`[attrs | _renderCloud] _renderCloud key=${key}`, `Work with chart=${chart}`);
                        chart.data.labels = labels;
                        chart.data.datasets[0].data = data;
                        chart.data.datasets[0].color = color;
                        chart.data.datasets[0].counts = counts;
                        console.log(`[attrs | _renderCloud] _renderCloud key=${key}`, "Data Updated with", {
                            labels: labels,
                            data: data,
                            color: color,
                        });
                        chart.update();
                        console.log(`[attrs | _renderCloud] _renderCloud key=${key}`, "Updated!");
                        return;
                    }

                    cloudCharts[key] = new Chart(canvas, {
                        type: "wordCloud",
                        data: {
                            labels: labels,
                            datasets: [{
                                label: "",
                                data: data,
                                color: color,
                                counts: counts,
                                minRotation: 0,
                                maxRotation: 0,
                                padding: 8,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                title: { display: false },
                                tooltip: {
                                    backgroundColor: "#1A233A",
                                    titleColor: "#E2E8F0",
                                    bodyColor: "#E2E8F0",
                                    borderColor: "rgba(167,139,250,0.3)",
                                    borderWidth: 1,
                                    callbacks: {
                                        label: (ctx) => {
                                            const counts = ctx.dataset.counts ?? [];
                                            return `${counts[ctx.dataIndex] ?? ''}`;
                                        },
                                    },
                                },
                            },
                        }
                    });
                },
                renderSingleBar(attrKey) {
                    console.log(`[attrs | renderSingleBar] Render start, key=${attrKey}`);
                    this._renderBar(
                        attrKey,
                        this.$refs[`bar-${attrKey}`],
                        this.getHistItems(attrKey),
                    );
                    console.log(`[attrs | renderSingleBar] Render end, key=${attrKey}`);
                },
                renderSingleCloud(attrKey) {
                    console.log(`[attrs | renderSingleCloud] Render start, key=${attrKey}`);
                    this._renderCloud(
                        attrKey,
                        this.$refs[`cloud-${attrKey}`],
                        this.getCloudItems(attrKey),
                    );
                    console.log(`[attrs | renderSingleCloud] Render end, key=${attrKey}`);
                },
                destroy() {
                    this._deleteAllBars();
                }
            }
        });

        Alpine.data("vorDetailOverlay", (opts = {}) => ({
            editing: Boolean(opts.editing),
            globalEdit: Boolean(opts.globalEdit),
            workType: opts.workType || "",
            workId: opts.workId || null,
            filmType: opts.filmType || "movie",
            title: opts.title || "",
            description: opts.description || "",
            releaseDate: opts.releaseDate || "",
            ageRating: opts.ageRating || "",
            externalLink: opts.externalLink || "",
            pages: opts.pages == null ? "" : opts.pages,
            durationMinutes: opts.durationMinutes == null ? "" : opts.durationMinutes,
            episodeCount: opts.episodeCount == null ? "" : opts.episodeCount,
            coverPreview: opts.coverUrl || "",
            coverCleared: false,
            coverWarning: "",
            coverFile: null,
            authors: opts.authors || [],
            genres: opts.genres || [],
            tags: opts.tags || [],
            platforms: opts.platforms || [],
            catalog: opts.catalog || {},
            relations: opts.relations || [],
            relationTypes: opts.relationTypes || [],
            ageChoices: opts.ageChoices || [],
            saveUrl: opts.saveUrl || "",
            relationSearchUrl: opts.relationSearchUrl || "",
            pickerKind: null,
            pickerQuery: "",
            pickerSelected: {},
            ageOpen: false,
            dateOpen: false,
            dateCursor: null,
            ...datePickerApi(),
            linkOpen: false,
            relAdding: false,
            relQuery: "",
            relResults: [],
            relPick: null,
            relPickType: "other",
            relTypeEdit: null,
            leaveConfirmOpen: false,
            attachOpen: false,
            saving: false,
            leaveChanges: [],
            leaveAction: null,
            snapshot: "",
            owned: Boolean(opts.owned),
            ownedPlatformIds: opts.ownedPlatformIds || [],
            status: opts.status || "planning",
            statusChoices: opts.statusChoices || [],
            statusOpen: false,
            rating: Number(opts.rating || 0),
            hoverRating: 0,
            isHidden: Boolean(opts.isHidden),
            progress: Number(opts.progress || 0),
            progressMax: opts.progressMax == null ? null : Number(opts.progressMax),
            progressUnit: opts.progressUnit || "",
            progressStep: Number(opts.progressStep || 1),
            progressEditing: false,
            progressHover: false,
            progressDraft: "",
            timesCompleted: Number(opts.timesCompleted || 0),
            lastCompletedDate: opts.lastCompletedDate || "",
            counterEditing: false,
            counterHover: false,
            counterDraft: "",
            quickUrl: opts.quickUrl || "",
            listUrl: opts.listUrl || "",
            attachUrl: opts.attachUrl || "",
            init() {
                this.dateCursor = this.releaseDate ? new Date(`${this.releaseDate}T00:00:00`) : new Date();
                this.snapshot = this.serializeDraft();
            },
            startEdit() {
                this.editing = true;
                this.coverWarning = "";
                this.snapshot = this.serializeDraft();
            },
            cancelEdit() {
                this.leaveOr(() => this.revertEdit());
            },
            revertEdit() {
                const data = JSON.parse(this.snapshot || "{}");
                this.title = data.title || "";
                this.description = data.description || "";
                this.releaseDate = data.releaseDate || "";
                this.ageRating = data.ageRating || "";
                this.externalLink = data.externalLink || "";
                this.pages = data.pages ?? "";
                this.durationMinutes = data.durationMinutes ?? "";
                this.episodeCount = data.episodeCount ?? "";
                this.authors = data.authors || [];
                this.genres = data.genres || [];
                this.tags = data.tags || [];
                this.platforms = data.platforms || [];
                this.relations = data.relations || [];
                this.coverPreview = data.coverPreview || "";
                this.coverCleared = false;
                this.coverFile = null;
                this.coverWarning = "";
                this.relAdding = false;
                this.editing = false;
                this.leaveConfirmOpen = false;
            },
            serializeDraft() {
                return JSON.stringify({
                    title: this.title,
                    description: this.description,
                    releaseDate: this.releaseDate,
                    ageRating: this.ageRating,
                    externalLink: this.externalLink,
                    pages: this.pages,
                    durationMinutes: this.durationMinutes,
                    episodeCount: this.episodeCount,
                    authors: this.authors,
                    genres: this.genres,
                    tags: this.tags,
                    platforms: this.platforms,
                    relations: this.relations,
                    coverPreview: this.coverPreview,
                    coverCleared: this.coverCleared,
                    coverName: this.coverFile?.name || "",
                });
            },
            dirtyChanges() {
                if (!this.editing) {
                    return [];
                }
                const labels = {
                    title: "Название",
                    description: "Описание",
                    releaseDate: "Дата релиза",
                    ageRating: "Возрастной рейтинг",
                    externalLink: "Ссылка",
                    pages: "Страницы",
                    durationMinutes: "Длительность",
                    episodeCount: "Эпизоды",
                    authors: "Авторы",
                    genres: "Жанры",
                    tags: "Теги",
                    platforms: "Платформы",
                    relations: "Связи",
                };
                const before = JSON.parse(this.snapshot || "{}");
                const after = JSON.parse(this.serializeDraft());
                const changes = [];
                Object.keys(labels).forEach((key) => {
                    if (JSON.stringify(before[key] ?? "") !== JSON.stringify(after[key] ?? "")) {
                        changes.push(labels[key]);
                    }
                });
                if (this.coverFile || this.coverCleared) {
                    changes.push("Обложка");
                }
                return changes;
            },
            tryLeave(proceed) {
                const changes = this.dirtyChanges();
                if (!changes.length) {
                    proceed();
                    return true;
                }
                this.leaveChanges = changes;
                this.leaveAction = proceed;
                this.leaveConfirmOpen = true;
                return false;
            },
            leaveOr(proceed) {
                this.tryLeave(proceed);
            },
            confirmLeave() {
                const action = this.leaveAction;
                this.leaveConfirmOpen = false;
                this.leaveAction = null;
                this.editing = false;
                if (typeof action === "function") {
                    action();
                }
            },
            authorIds() {
                return this.authors.map((item) => item.id);
            },
            genreIds() {
                return this.genres.map((item) => item.id);
            },
            tagIds() {
                return this.tags.map((item) => item.id);
            },
            platformIds() {
                return this.platforms.map((item) => item.id);
            },
            relationsJson() {
                return JSON.stringify(
                    this.relations.map((item) => ({
                        id: item.id || null,
                        relation_type: item.relation_type,
                        type_key: item.type_key,
                        work_id: item.work_id,
                    }))
                );
            },
            ageLabel() {
                const found = this.ageChoices.find((item) => item.value === this.ageRating);
                return found ? found.label : "Возрастной рейтинг";
            },
            setAgeRating(value) {
                this.ageRating = value;
                this.ageOpen = false;
            },
            openLinkEditor() {
                this.linkOpen = !this.linkOpen;
                if (this.linkOpen) {
                    this.$nextTick(() => {
                        const input = this.$refs.linkInput;
                        if (input) {
                            input.focus();
                            input.select();
                        }
                    });
                }
            },
            removeChip(kind, id) {
                this[kind] = this[kind].filter((item) => item.id !== id);
            },
            togglePicker(kind) {
                if (this.pickerKind === kind) {
                    this.closePicker();
                    return;
                }
                this.pickerKind = kind;
                this.pickerQuery = "";
                this.pickerSelected = {};
            },
            closePicker() {
                this.pickerKind = null;
                this.pickerQuery = "";
                this.pickerSelected = {};
            },
            pickerOptions(kind) {
                const selected = new Set((this[kind] || []).map((item) => item.id));
                const query = String(this.pickerQuery || "").trim().toLowerCase();
                return (this.catalog[kind] || []).filter((item) => {
                    if (selected.has(item.id)) {
                        return false;
                    }
                    return !query || item.name.toLowerCase().includes(query);
                });
            },
            addPickerItem(kind, opt) {
                if (this[kind].some((item) => item.id === opt.id)) {
                    return;
                }
                this[kind] = [...this[kind], opt];
            },
            isPlatformOwned(id) {
                return this.ownedPlatformIds.map(Number).includes(Number(id));
            },
            canTogglePlatform() {
                return this.owned && !this.editing;
            },
            platformOff(id) {
                return this.owned && !this.isPlatformOwned(id);
            },
            togglePlatform(id) {
                if (!this.canTogglePlatform()) {
                    return;
                }
                id = Number(id);
                const next = this.ownedPlatformIds.map(Number);
                const index = next.indexOf(id);
                if (index > -1) {
                    next.splice(index, 1);
                } else {
                    next.push(id);
                }
                this.ownedPlatformIds = next;
                this.saveField("owned_platform", id);
            },
            placeChipTip(el, tip) {
                if (!tip) {
                    return;
                }
                const tipEl = el.querySelector(".vor-chip-tip");
                if (!tipEl) {
                    return;
                }
                const rect = el.getBoundingClientRect();
                tipEl.style.left = `${rect.left}px`;
                tipEl.style.top = `${rect.bottom + 6}px`;
            },
            async onCoverSelected(event) {
                const file = event.target.files && event.target.files[0];
                if (!file) {
                    return;
                }
                const result = await cropCoverFile(file);
                this.coverFile = result.file;
                this.coverCleared = false;
                this.coverPreview = URL.createObjectURL(result.file);
                this.coverWarning = result.cropped
                    ? `Обложка была обрезана для соответствия размера: исходный ${result.srcW}×${result.srcH}, итоговый ${result.outW}×${result.outH}`
                    : "";
                this.assignCoverInput(result.file);
            },
            assignCoverInput(file) {
                const input = this.$refs.coverInput;
                if (!input || typeof DataTransfer === "undefined") {
                    return;
                }
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
            },
            clearCover() {
                this.coverPreview = "";
                this.coverFile = null;
                this.coverCleared = true;
                this.coverWarning = "";
                if (this.$refs.coverInput) {
                    this.$refs.coverInput.value = "";
                }
            },
            allowedRelationTypes(otherType) {
                return this.relationTypes.filter((opt) => {
                    if (opt.value === "other") {
                        return true;
                    }
                    if (opt.value === "adaptation") {
                        return otherType && otherType !== this.workType;
                    }
                    return otherType === this.workType;
                });
            },
            relationKey(item) {
                return `${item.id || "new"}-${item.type_key}-${item.work_id}`;
            },
            relationLabelFor(type, direction) {
                const found = this.relationTypes.find((item) => item.value === type);
                if (type === "sequel") {
                    return direction === "in" ? "Предыстория" : "Продолжение";
                }
                if (type === "spin_off") {
                    return direction === "in" ? "Оригинал" : "Спин-офф";
                }
                if (type === "adaptation") {
                    return direction === "in" ? "Первоисточник" : "Адаптация";
                }
                if (type === "remake") {
                    return direction === "in" ? "Оригинал" : "Ремейк";
                }
                return found ? found.label : "Связано";
            },
            toggleRelationType(item) {
                const key = this.relationKey(item);
                this.relTypeEdit = this.relTypeEdit === key ? null : key;
            },
            setRelationType(item, value) {
                item.relation_type = value;
                item.label = this.relationLabelFor(value, item.direction || "out");
                this.relTypeEdit = null;
            },
            removeRelation(item) {
                this.relations = this.relations.filter((rel) => rel !== item);
            },
            startRelationAdd() {
                this.relAdding = true;
                this.relQuery = "";
                this.relResults = [];
                this.relPick = null;
                this.relPickType = "other";
            },
            cancelRelationAdd() {
                this.relAdding = false;
                this.relPick = null;
                this.relQuery = "";
                this.relResults = [];
            },
            searchRelatedWorks() {
                const query = String(this.relQuery || "").trim();
                if (!query || !this.relationSearchUrl) {
                    this.relResults = [];
                    return;
                }
                const params = new URLSearchParams({
                    q: query,
                    exclude_type: this.workType,
                    exclude_id: String(this.workId || ""),
                });
                fetch(`${this.relationSearchUrl}?${params.toString()}`, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                })
                    .then((response) => (response.ok ? response.json() : { results: [] }))
                    .then((data) => {
                        const taken = new Set(
                            this.relations.map((item) => `${item.type_key}-${item.work_id}`)
                        );
                        this.relResults = (data.results || []).filter(
                            (item) => !taken.has(`${item.type_key}-${item.work_id}`)
                        );
                    });
            },
            commitRelationAdd() {
                if (!this.relPick) {
                    return;
                }
                const allowed = this.allowedRelationTypes(this.relPick.type_key).map((item) => item.value);
                const type = allowed.includes(this.relPickType) ? this.relPickType : allowed[0];
                this.relations = [
                    ...this.relations,
                    {
                        id: null,
                        title: this.relPick.title,
                        cover_url: this.relPick.cover_url,
                        icon: this.relPick.icon,
                        type_key: this.relPick.type_key,
                        work_id: this.relPick.work_id,
                        relation_type: type,
                        direction: "out",
                        label: this.relationLabelFor(type, "out"),
                    },
                ];
                this.cancelRelationAdd();
            },
            openRelated(item) {
                this.leaveOr(() => {
                    htmx.ajax("GET", `/library/artworks/${item.type_key}/${item.work_id}/`, {
                        target: "#vor-overlay",
                        swap: "innerHTML",
                    });
                });
            },
            prepareSubmit() {
                if (this.coverFile) {
                    this.assignCoverInput(this.coverFile);
                }
            },
            saveEdit() {
                this.prepareSubmit();
                this.$nextTick(() => this.$refs.editForm?.requestSubmit());
            },
            statusLabel() {
                const found = this.statusChoices.find((item) => item.value === this.status);
                return found ? found.label : this.status;
            },
            setStatus(value) {
                this.statusOpen = false;
                if (this.status === value) {
                    return;
                }
                this.status = value;
                if (value === "completed" && this.progressMax != null) {
                    this.progress = this.progressMax;
                }
                if (value === "in_progress") {
                    this.progress = 0;
                }
                this.saveField("status", value);
            },
            progressValueLabel() {
                const value = Number(this.progress || 0);
                return value === Math.round(value) ? String(Math.round(value)) : String(Math.round(value * 10) / 10);
            },
            progressSuffix() {
                if (this.progressMax != null) {
                    return `/${this.progressMax} ${this.progressUnit}`.trim();
                }
                return this.progressUnit;
            },
            progressCh() {
                if (this.progressMax != null) {
                    return String(Math.floor(this.progressMax)).length;
                }
                return 4;
            },
            displayRating() {
                return this.hoverRating || this.rating || 0;
            },
            ratingLabel() {
                const value = this.displayRating();
                return value ? String(value) : "—";
            },
            starState(star) {
                const shown = this.displayRating();
                const fullAt = star * 2;
                if (shown >= fullAt) {
                    return "is-full";
                }
                if (shown === fullAt - 1) {
                    return "is-half";
                }
                return "is-empty";
            },
            setRating(value) {
                this.rating = this.rating === value ? 0 : value;
                this.saveField("rating", this.rating);
            },
            startProgressEdit() {
                this.progressDraft = this.progressValueLabel();
                this.progressEditing = true;
                this.progressHover = true;
                this.$nextTick(() => this.$refs.progressInput?.focus());
            },
            cancelProgressEdit() {
                this.progressEditing = false;
                this.progressHover = false;
            },
            commitProgress() {
                if (!this.progressEditing) {
                    return;
                }
                this.progressEditing = false;
                this.progressHover = false;
                const parsed = Number(String(this.progressDraft).replace(",", "."));
                if (Number.isNaN(parsed)) {
                    return;
                }
                this.applyProgress(parsed);
            },
            nudgeProgress(direction) {
                this.applyProgress(this.progress + direction * this.progressStep);
            },
            applyProgress(value) {
                this.progress = this.clampProgress(value);
                if (this.progressMax != null && this.progress >= this.progressMax) {
                    this.status = "completed";
                }
                this.saveField("progress", this.progress);
            },
            clampProgress(value) {
                let next = Math.max(0, value);
                if (this.progressMax != null) {
                    next = Math.min(this.progressMax, next);
                }
                return Math.round(next * 10) / 10;
            },
            startCounterEdit() {
                this.counterDraft = String(this.timesCompleted || 0);
                this.counterEditing = true;
                this.counterHover = true;
                this.$nextTick(() => this.$refs.counterInput?.focus());
            },
            cancelCounterEdit() {
                this.counterEditing = false;
                this.counterHover = false;
            },
            commitCounter() {
                if (!this.counterEditing) {
                    return;
                }
                this.counterEditing = false;
                this.counterHover = false;
                const parsed = parseInt(this.counterDraft, 10);
                if (Number.isNaN(parsed)) {
                    return;
                }
                this.timesCompleted = Math.max(0, parsed);
                this.saveField("times_completed", this.timesCompleted);
            },
            applyQuickResult(data) {
                if (!data || typeof data !== "object") {
                    return;
                }
                if (data.status) {
                    this.status = data.status;
                }
                if (data.progress != null) {
                    this.progress = Number(data.progress);
                }
                if (data.times_completed != null) {
                    this.timesCompleted = Number(data.times_completed);
                }
                if (Object.prototype.hasOwnProperty.call(data, "last_completed_date")) {
                    this.lastCompletedDate = data.last_completed_date || "";
                }
                if (Array.isArray(data.owned_platform_ids)) {
                    this.ownedPlatformIds = data.owned_platform_ids.map(Number);
                }
            },
            saveField(field, value) {
                if (!this.quickUrl || this.attachOpen) {
                    return;
                }
                const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
                const body = new URLSearchParams({ field, value: String(value) });
                fetch(this.quickUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": token || "",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body,
                })
                    .then((response) => (response.ok ? response.json() : null))
                    .then((data) => {
                        this.applyQuickResult(data);
                        this.refreshList();
                    });
            },
            refreshList() {
                window.Alpine?.store("vorArtworks")?.reloadList();
            },
            startAttach() {
                this.status = "planning";
                this.statusOpen = false;
                this.rating = 0;
                this.hoverRating = 0;
                this.progress = 0;
                this.progressEditing = false;
                this.progressHover = false;
                this.attachOpen = true;
            },
            csrfToken() {
                return document.querySelector("[name=csrfmiddlewaretoken]")?.value
                    || getCookie("csrftoken");
            },
            async saveAttach() {
                if (this.saving || !this.attachUrl || !this.workId) {
                    return;
                }
                const body = new URLSearchParams({
                    work_type: this.workType,
                    work_id: String(this.workId),
                    status: this.status || "planning",
                    rating: this.rating ? String(this.rating) : "",
                    progress: String(this.progress || 0),
                });
                this.saving = true;
                try {
                    const response = await fetch(this.attachUrl, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": this.csrfToken(),
                            "X-Requested-With": "XMLHttpRequest",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body,
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || !data.ok) {
                        return;
                    }
                    this.attachOpen = false;
                    this.refreshList();
                    htmx.ajax("GET", `/library/artworks/${this.workType}/${this.workId}/`, {
                        target: "#vor-overlay",
                        swap: "innerHTML",
                    });
                } finally {
                    this.saving = false;
                }
            },
        }));

        Alpine.data("vorChipOverflow", () => ({
            hiddenCount: 0,
            visibleCount: 0,
            popupOpen: false,
            overlayData() {
                const root = this.$el.closest(".vor-overlay");
                return root && window.Alpine ? Alpine.$data(root) : null;
            },
            canTogglePlatform() {
                return Boolean(this.overlayData()?.canTogglePlatform());
            },
            platformOff(id) {
                return Boolean(this.overlayData()?.platformOff(id));
            },
            togglePlatform(id) {
                this.overlayData()?.togglePlatform(id);
            },
            init() {
                this._ro = new ResizeObserver(() => this.fit());
                this._ro.observe(this.$el);
                this.$nextTick(() => this.fit());
            },
            destroy() {
                this._ro?.disconnect();
            },
            togglePopup() {
                this.popupOpen = !this.popupOpen;
                if (this.popupOpen) {
                    this.$nextTick(() => this.placePopup());
                }
            },
            fit() {
                const root = this.$el;
                const chips = [...root.querySelectorAll("[data-chip]")];
                const more = this.$refs.more;
                chips.forEach((chip) => {
                    chip.style.display = "";
                });
                const available = root.clientWidth;
                if (available <= 0) {
                    return;
                }
                const gap = parseFloat(getComputedStyle(root).columnGap || getComputedStyle(root).gap) || 6.4;
                let total = 0;
                chips.forEach((chip, index) => {
                    total += chip.offsetWidth + (index ? gap : 0);
                });
                if (total <= available) {
                    this.visibleCount = chips.length;
                    this.hiddenCount = 0;
                    return;
                }
                let moreWidth = 48;
                const moreWrap = this.$refs.moreWrap;
                if (moreWrap) {
                    const prevDisplay = moreWrap.style.display;
                    moreWrap.style.display = "inline-flex";
                    moreWrap.style.visibility = "hidden";
                    moreWrap.style.position = "absolute";
                    moreWidth = (more && more.offsetWidth) || moreWrap.offsetWidth || moreWidth;
                    moreWrap.style.display = prevDisplay;
                    moreWrap.style.visibility = "";
                    moreWrap.style.position = "";
                } else if (more) {
                    const prevDisplay = more.style.display;
                    more.style.display = "inline-flex";
                    more.style.visibility = "hidden";
                    more.style.position = "absolute";
                    moreWidth = more.offsetWidth || moreWidth;
                    more.style.display = prevDisplay;
                    more.style.visibility = "";
                    more.style.position = "";
                }
                let used = 0;
                let visible = 0;
                for (let i = 0; i < chips.length; i += 1) {
                    const next = used + (i ? gap : 0) + chips[i].offsetWidth;
                    if (next + gap + moreWidth <= available) {
                        used = next;
                        visible = i + 1;
                    } else {
                        break;
                    }
                }
                chips.forEach((chip, index) => {
                    chip.style.display = index < visible ? "" : "none";
                });
                this.visibleCount = visible;
                this.hiddenCount = chips.length - visible;
            },
            placeTip(chip) {
                const tip = chip.querySelector(".vor-chip-tip");
                if (!tip) {
                    return;
                }
                const pad = 8;
                const chipRect = chip.getBoundingClientRect();
                tip.style.position = "fixed";
                tip.style.left = `${chipRect.right + 6}px`;
                tip.style.top = `${chipRect.top + chipRect.height / 2}px`;
                tip.style.right = "auto";
                tip.style.bottom = "auto";
                tip.style.transform = "translateY(-50%)";
                this.$nextTick(() => {
                    let rect = tip.getBoundingClientRect();
                    if (rect.right > window.innerWidth - pad) {
                        tip.style.left = `${Math.max(pad, chipRect.left - rect.width - 6)}px`;
                        rect = tip.getBoundingClientRect();
                    }
                    let shiftY = 0;
                    if (rect.bottom > window.innerHeight - pad) {
                        shiftY = window.innerHeight - pad - rect.bottom;
                    }
                    if (rect.top + shiftY < pad) {
                        shiftY = pad - rect.top;
                    }
                    tip.style.transform = `translateY(calc(-50% + ${shiftY}px))`;
                });
            },
            placePopup() {
                const popup = this.$refs.popup;
                if (!popup) {
                    return;
                }
                popup.style.top = "calc(100% + 4px)";
                popup.style.left = "0";
                popup.style.right = "auto";
                popup.style.bottom = "auto";
                const pad = 8;
                const rect = popup.getBoundingClientRect();
                if (rect.right > window.innerWidth - pad) {
                    popup.style.left = "auto";
                    popup.style.right = "0";
                }
                if (rect.bottom > window.innerHeight - pad) {
                    popup.style.top = "auto";
                    popup.style.bottom = "calc(100% + 4px)";
                }
            },
        }));

        Alpine.data("vorAddOverlay", (opts = {}) => ({
            workType: opts.workType || "book",
            title: "",
            description: "",
            releaseDate: "",
            ageRating: "",
            externalLink: "",
            pages: "",
            durationMinutes: "",
            episodeCount: "",
            filmType: "movie",
            coverPreview: "",
            coverWarning: "",
            coverFile: null,
            authors: [],
            genres: [],
            tags: [],
            platforms: [],
            catalogs: opts.catalogs || {},
            ageChoices: opts.ageChoices || [],
            statusChoices: opts.statusChoices || [],
            saveUrl: opts.saveUrl || "",
            searchUrl: opts.searchUrl || "",
            previewUrl: opts.previewUrl || "",
            attachUrl: opts.attachUrl || "",
            listUrl: opts.listUrl || "",
            relationSearchUrl: opts.relationSearchUrl || "",
            relationTypes: opts.relationTypes || [],
            relations: [],
            relAdding: false,
            relQuery: "",
            relResults: [],
            relPick: null,
            relPickType: "other",
            relTypeEdit: null,
            selectedWorkId: null,
            alreadyOwned: false,
            createdWorkId: null,
            createdWorkType: "",
            justCreated: false,
            phase: "form",
            saving: false,
            errors: {},
            formError: "",
            doneMessage: "",
            dateOpen: false,
            dateCursor: new Date(),
            ...datePickerApi(),
            ageOpen: false,
            status: "planning",
            statusOpen: false,
            rating: 0,
            hoverRating: 0,
            progress: 0,
            progressMax: null,
            progressUnit: "",
            progressStep: 1,
            progressEditing: false,
            progressHover: false,
            progressDraft: "",
            searchTimer: null,
            get catalog() {
                return this.catalogs[this.workType] || {
                    authors: [],
                    genres: [],
                    tags: [],
                    platforms: [],
                };
            },
            init() {
                this.dateCursor = new Date();
            },
            setType(type) {
                if (this.workType === type) {
                    return;
                }
                this.workType = type;
                this.genres = [];
                if (type !== "game") {
                    this.platforms = [];
                }
                this.clearSelection();
                this.refreshSearch();
            },
            onTitleInput() {
                this.clearSelection();
                this.scheduleSearch();
            },
            scheduleSearch() {
                clearTimeout(this.searchTimer);
                this.searchTimer = setTimeout(() => this.refreshSearch(), 280);
            },
            onSuggestionClick(event) {
                const button = event.target.closest(".vor-suggestion-item");
                if (!button) {
                    return;
                }
                this.selectWork(button.dataset.workId, button.dataset.previewUrl);
            },
            selectWork(id, previewUrl) {
                this.selectedWorkId = Number(id);
                this.createdWorkId = Number(id);
                this.createdWorkType = this.workType;
                this.justCreated = false;
                const url = previewUrl || `${this.previewUrl}?type=${this.workType}&work_id=${id}`;
                htmx.ajax("GET", url, {
                    target: "#add-preview",
                    swap: "innerHTML",
                });
                this.clearSuggestions();
            },
            onPreviewClick(event) {
                const button = event.target.closest("[data-attach-preview]");
                if (!button) {
                    return;
                }
                this.startAttachFromPreview(button.closest(".vor-preview-card"));
            },
            startAttachFromPreview(card) {
                if (!card) {
                    return;
                }
                const rawMax = card.dataset.progressMax;
                this.progressMax = rawMax === "" || rawMax == null ? null : Number(rawMax);
                this.progressUnit = card.dataset.progressUnit || "";
                this.progressStep = Number(card.dataset.progressStep || 1);
                this.createdWorkId = this.selectedWorkId;
                this.createdWorkType = this.workType;
                this.resetAttachFields();
                this.phase = "attach";
            },
            clearSelection() {
                this.selectedWorkId = null;
                this.alreadyOwned = false;
                if (this.phase === "form") {
                    this.createdWorkId = this.justCreated ? this.createdWorkId : null;
                }
                const preview = document.getElementById("add-preview");
                if (preview) {
                    preview.innerHTML = "";
                }
            },
            clearSuggestions() {
                const suggestions = document.getElementById("work-suggestions");
                if (suggestions) {
                    suggestions.innerHTML = "";
                }
            },
            refreshSearch() {
                const query = String(this.title || "").trim();
                if (!query || !this.searchUrl) {
                    this.clearSuggestions();
                    return;
                }
                const params = new URLSearchParams({
                    work_type: this.workType,
                    q: query,
                });
                htmx.ajax("GET", `${this.searchUrl}?${params.toString()}`, {
                    target: "#work-suggestions",
                    swap: "innerHTML",
                });
            },
            filterCatalog(kind, query) {
                const q = String(query || "").trim().toLowerCase();
                return (this.catalog[kind] || []).filter((item) => (
                    !q || String(item.name || "").toLowerCase().includes(q)
                ));
            },
            hasAttr(kind, id) {
                return (this[kind] || []).some((item) => Number(item.id) === Number(id));
            },
            toggleAttr(kind, opt) {
                if (this.hasAttr(kind, opt.id)) {
                    this[kind] = this[kind].filter((item) => Number(item.id) !== Number(opt.id));
                    return;
                }
                this[kind] = [...this[kind], opt];
            },
            setAgeRating(value) {
                this.ageRating = value;
                this.ageOpen = false;
            },
            async onCoverSelected(event) {
                const file = event.target.files && event.target.files[0];
                if (!file) {
                    return;
                }
                const result = await cropCoverFile(file);
                this.coverFile = result.file;
                this.coverPreview = URL.createObjectURL(result.file);
                this.coverWarning = result.cropped
                    ? `Обложка была обрезана для соответствия размера: исходный ${result.srcW}×${result.srcH}, итоговый ${result.outW}×${result.outH}`
                    : "";
                this.assignCoverInput(result.file);
            },
            assignCoverInput(file) {
                const input = this.$refs.coverInput;
                if (!input || typeof DataTransfer === "undefined") {
                    return;
                }
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
            },
            clearCover() {
                this.coverPreview = "";
                this.coverFile = null;
                this.coverWarning = "";
                if (this.$refs.coverInput) {
                    this.$refs.coverInput.value = "";
                }
            },
            isRequired(name) {
                if (name === "title") {
                    return true;
                }
                if (name === "pages") {
                    return this.workType === "book";
                }
                if (name === "duration_minutes") {
                    return this.workType === "film";
                }
                if (name === "episode_count") {
                    return this.workType === "film" && this.filmType === "tv_show";
                }
                return false;
            },
            isEmpty(name) {
                if (name === "title") {
                    return !String(this.title || "").trim();
                }
                if (name === "pages") {
                    return !this.pages;
                }
                if (name === "duration_minutes") {
                    return !this.durationMinutes;
                }
                if (name === "episode_count") {
                    return !this.episodeCount;
                }
                return false;
            },
            showRequired(name) {
                return this.isRequired(name) && this.isEmpty(name);
            },
            titleInvalid() {
                return this.alreadyOwned || this.showRequired("title") || Boolean(this.fieldError("title"));
            },
            titleBanner() {
                if (this.alreadyOwned) {
                    return "Это произведение уже есть в вашем списке";
                }
                return this.fieldError("title") || this.fieldError("__all__");
            },
            fieldError(name) {
                if (this.isRequired(name) && !this.isEmpty(name)) {
                    return "";
                }
                const items = this.errors[name];
                if (!items || !items.length) {
                    return "";
                }
                return items[0].message || items[0] || "";
            },
            validateDraft() {
                const errors = {};
                if (this.showRequired("title")) {
                    errors.title = [{ message: "Укажите название" }];
                }
                if (this.showRequired("pages")) {
                    errors.pages = [{ message: "Укажите количество страниц" }];
                }
                if (this.showRequired("duration_minutes")) {
                    errors.duration_minutes = [{ message: "Укажите длительность" }];
                }
                if (this.showRequired("episode_count")) {
                    errors.episode_count = [{ message: "Укажите количество эпизодов" }];
                }
                this.errors = errors;
                this.formError = "";
                return !Object.keys(errors).length;
            },
            appendIds(body, name, items) {
                (items || []).forEach((item) => body.append(name, String(item.id)));
            },
            csrfToken() {
                return this.$refs.createForm?.querySelector("[name=csrfmiddlewaretoken]")?.value
                    || document.querySelector("[name=csrfmiddlewaretoken]")?.value
                    || getCookie("csrftoken");
            },
            async saveWork() {
                if (this.saving || !this.validateDraft()) {
                    return;
                }
                if (this.coverFile) {
                    this.assignCoverInput(this.coverFile);
                }
                const body = new FormData();
                body.append("work_type", this.workType);
                body.append("title", String(this.title || "").trim());
                body.append("description", this.description || "");
                body.append("release_date", this.releaseDate || "");
                body.append("age_rating", this.ageRating || "");
                body.append("external_link", this.externalLink || "");
                if (this.workType === "book") {
                    body.append("pages", this.pages);
                }
                if (this.workType === "film") {
                    body.append("film_type", this.filmType);
                    body.append("duration_minutes", this.durationMinutes);
                    if (this.filmType === "tv_show") {
                        body.append("episode_count", this.episodeCount);
                    }
                }
                this.appendIds(body, "authors", this.authors);
                this.appendIds(body, "genres", this.genres);
                this.appendIds(body, "tags", this.tags);
                if (this.workType === "game") {
                    this.appendIds(body, "platforms", this.platforms);
                }
                if (this.coverFile) {
                    body.append("cover", this.coverFile);
                }
                body.append("relations_json", this.relationsJson());
                this.saving = true;
                this.formError = "";
                try {
                    const response = await fetch(this.saveUrl, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": this.csrfToken(),
                            "X-Requested-With": "XMLHttpRequest",
                        },
                        body,
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || !data.ok) {
                        this.errors = data.errors || {};
                        this.formError = this.fieldError("__all__") || "Не удалось сохранить произведение";
                        return;
                    }
                    this.createdWorkId = data.work_id;
                    this.createdWorkType = data.work_type || this.workType;
                    this.justCreated = true;
                    this.progressMax = data.progressMax == null ? null : Number(data.progressMax);
                    this.progressUnit = data.progressUnit || "";
                    this.progressStep = Number(data.progressStep || 1);
                    this.resetAttachFields();
                    this.phase = "choice";
                } catch (error) {
                    this.formError = "Не удалось сохранить произведение";
                } finally {
                    this.saving = false;
                }
            },
            resetAttachFields() {
                this.status = "planning";
                this.statusOpen = false;
                this.rating = 0;
                this.hoverRating = 0;
                this.progress = 0;
                this.progressEditing = false;
                this.progressHover = false;
            },
            finishCreate(kind) {
                this.doneMessage = kind === "list"
                    ? "Произведение создано и добавлено в ваш список."
                    : "Произведение успешно сохранено в базу данных.";
                this.phase = "done";
                this.refreshList();
            },
            async saveAttach() {
                if (this.saving || !this.createdWorkId || !this.attachUrl) {
                    return;
                }
                const body = new URLSearchParams({
                    work_type: this.createdWorkType || this.workType,
                    work_id: String(this.createdWorkId),
                    status: this.status || "planning",
                    rating: this.rating ? String(this.rating) : "",
                    progress: String(this.progress || 0),
                });
                this.saving = true;
                try {
                    const response = await fetch(this.attachUrl, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": this.csrfToken(),
                            "X-Requested-With": "XMLHttpRequest",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body,
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || !data.ok) {
                        this.formError = "Не удалось добавить произведение в список";
                        return;
                    }
                    this.doneMessage = this.justCreated
                        ? "Произведение создано и добавлено в ваш список."
                        : "Произведение добавлено в ваш список.";
                    this.phase = "done";
                    this.refreshList();
                } catch (error) {
                    this.formError = "Не удалось добавить произведение в список";
                } finally {
                    this.saving = false;
                }
            },
            dismissModal() {
                if (this.phase === "attach" && this.justCreated) {
                    this.phase = "choice";
                    return;
                }
                if (this.phase === "attach") {
                    this.phase = "form";
                    return;
                }
                if (this.phase === "choice") {
                    this.finishCreate("db");
                }
            },
            goToList() {
                this.refreshList();
                window.Alpine?.store("vorArtworks")?.closeOverlay();
            },
            resetForm() {
                this.title = "";
                this.description = "";
                this.releaseDate = "";
                this.ageRating = "";
                this.externalLink = "";
                this.pages = "";
                this.durationMinutes = "";
                this.episodeCount = "";
                this.filmType = "movie";
                this.authors = [];
                this.genres = [];
                this.tags = [];
                this.platforms = [];
                this.relations = [];
                this.cancelRelationAdd();
                this.clearCover();
                this.clearSelection();
                this.clearSuggestions();
                this.createdWorkId = null;
                this.createdWorkType = "";
                this.justCreated = false;
                this.errors = {};
                this.formError = "";
                this.alreadyOwned = false;
                this.doneMessage = "";
                this.resetAttachFields();
                this.phase = "form";
            },
            refreshList() {
                window.Alpine?.store("vorArtworks")?.reloadList();
            },
            statusLabel() {
                const found = this.statusChoices.find((item) => item.value === this.status);
                return found ? found.label : "Запланировано";
            },
            setStatus(value) {
                this.statusOpen = false;
                this.status = value;
                if (value === "completed" && this.progressMax != null) {
                    this.progress = this.progressMax;
                }
                if (value === "in_progress") {
                    this.progress = 0;
                }
            },
            displayRating() {
                return this.hoverRating || this.rating || 0;
            },
            ratingLabel() {
                const value = this.displayRating();
                return value ? String(value) : "—";
            },
            starState(star) {
                const shown = this.displayRating();
                const fullAt = star * 2;
                if (shown >= fullAt) {
                    return "is-full";
                }
                if (shown === fullAt - 1) {
                    return "is-half";
                }
                return "is-empty";
            },
            setRating(value) {
                this.rating = this.rating === value ? 0 : value;
            },
            startProgressEdit() {
                this.progressDraft = this.progressValueLabel();
                this.progressEditing = true;
                this.progressHover = true;
                this.$nextTick(() => this.$refs.progressInput?.focus());
            },
            cancelProgressEdit() {
                this.progressEditing = false;
                this.progressHover = false;
            },
            commitProgress() {
                if (!this.progressEditing) {
                    return;
                }
                this.progressEditing = false;
                this.progressHover = false;
                const parsed = Number(String(this.progressDraft).replace(",", "."));
                if (Number.isNaN(parsed)) {
                    return;
                }
                this.progress = this.clampProgress(parsed);
            },
            nudgeProgress(direction) {
                this.progress = this.clampProgress(this.progress + direction * this.progressStep);
            },
            progressValueLabel() {
                const value = Number(this.progress || 0);
                return value === Math.round(value) ? String(Math.round(value)) : String(Math.round(value * 10) / 10);
            },
            progressSuffix() {
                if (this.progressMax != null) {
                    return `/${this.progressMax} ${this.progressUnit}`.trim();
                }
                return this.progressUnit;
            },
            progressCh() {
                if (this.progressMax != null) {
                    return String(Math.floor(this.progressMax)).length;
                }
                return 4;
            },
            clampProgress(value) {
                let next = Math.max(0, value);
                if (this.progressMax != null) {
                    next = Math.min(this.progressMax, next);
                }
                return Math.round(next * 10) / 10;
            },
            allowedRelationTypes(otherType) {
                return this.relationTypes.filter((opt) => {
                    if (opt.value === "other") {
                        return true;
                    }
                    if (opt.value === "adaptation") {
                        return otherType && otherType !== this.workType;
                    }
                    return otherType === this.workType;
                });
            },
            relationKey(item) {
                return `${item.id || "new"}-${item.type_key}-${item.work_id}`;
            },
            relationLabelFor(type, direction) {
                const found = this.relationTypes.find((item) => item.value === type);
                if (type === "sequel") {
                    return direction === "in" ? "Предыстория" : "Продолжение";
                }
                if (type === "spin_off") {
                    return direction === "in" ? "Оригинал" : "Спин-офф";
                }
                if (type === "adaptation") {
                    return direction === "in" ? "Первоисточник" : "Адаптация";
                }
                if (type === "remake") {
                    return direction === "in" ? "Оригинал" : "Ремейк";
                }
                return found ? found.label : "Связано";
            },
            toggleRelationType(item) {
                const key = this.relationKey(item);
                this.relTypeEdit = this.relTypeEdit === key ? null : key;
            },
            setRelationType(item, value) {
                item.relation_type = value;
                item.label = this.relationLabelFor(value, item.direction || "out");
                this.relTypeEdit = null;
            },
            removeRelation(item) {
                this.relations = this.relations.filter((rel) => rel !== item);
            },
            startRelationAdd() {
                this.relAdding = true;
                this.relQuery = "";
                this.relResults = [];
                this.relPick = null;
                this.relPickType = "other";
            },
            cancelRelationAdd() {
                this.relAdding = false;
                this.relPick = null;
                this.relQuery = "";
                this.relResults = [];
            },
            searchRelatedWorks() {
                const query = String(this.relQuery || "").trim();
                if (!query || !this.relationSearchUrl) {
                    this.relResults = [];
                    return;
                }
                const params = new URLSearchParams({
                    q: query,
                    exclude_type: this.workType,
                    exclude_id: String(this.workId || ""),
                });
                fetch(`${this.relationSearchUrl}?${params.toString()}`, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                })
                    .then((response) => (response.ok ? response.json() : { results: [] }))
                    .then((data) => {
                        const taken = new Set(
                            this.relations.map((item) => `${item.type_key}-${item.work_id}`)
                        );
                        this.relResults = (data.results || []).filter(
                            (item) => !taken.has(`${item.type_key}-${item.work_id}`)
                        );
                    });
            },
            commitRelationAdd() {
                if (!this.relPick) {
                    return;
                }
                const allowed = this.allowedRelationTypes(this.relPick.type_key).map((item) => item.value);
                const type = allowed.includes(this.relPickType) ? this.relPickType : allowed[0];
                this.relations = [
                    ...this.relations,
                    {
                        id: null,
                        title: this.relPick.title,
                        cover_url: this.relPick.cover_url,
                        icon: this.relPick.icon,
                        type_key: this.relPick.type_key,
                        work_id: this.relPick.work_id,
                        relation_type: type,
                        direction: "out",
                        label: this.relationLabelFor(type, "out"),
                    },
                ];
                this.cancelRelationAdd();
            },
            relationsJson() {
                return JSON.stringify(
                    this.relations.map((item) => ({
                        id: item.id || null,
                        relation_type: item.relation_type,
                        type_key: item.type_key,
                        work_id: item.work_id,
                    }))
                );
            },
        }));
    });

    document.addEventListener("keydown", (event) => {
        const store = window.Alpine?.store("vorArtworks");
        if (!store) {
            return;
        }
        if (event.key === "Escape") {
            if (store.menu?.open) {
                store.closeMenu();
                return;
            }
            if (store.searchOpen) {
                store.closeSearch();
                return;
            }
            if (hasContent("vor-modal")) {
                store.closeModal();
                return;
            }
            const overlay = overlayAlpine();
            if (overlay?.attachOpen) {
                overlay.attachOpen = false;
                return;
            }
            if (overlay?.phase && overlay.phase !== "form") {
                overlay.dismissModal();
                return;
            }
            if (hasContent("vor-overlay")) {
                store.closeOverlay();
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
            if (hasContent("vor-modal") || hasContent("vor-overlay")) {
                return;
            }
            event.preventDefault();
            store.openPreview();
        }
    });

    document.addEventListener(
        "click",
        (event) => {
            const store = window.Alpine?.store("vorArtworks");
            if (!store?.deleteMode) {
                return;
            }
            const item = event.target.closest(".artwork-item");
            if (!item || event.target.closest(".artwork-row-delete, .artwork-tile-delete")) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const id = Number(item.dataset.uwId);
            if (id) {
                store.toggleSelected(id);
            }
        },
        true
    );

    document.body.addEventListener("vor:close-overlay", () => {
        const store = window.Alpine?.store("vorArtworks");
        if (!store) {
            return;
        }
        store.closeOverlay();
        store.closeModal();
        store.exitDeleteMode();
    });

    document.body.addEventListener("vor:reload-list", () => {
        window.Alpine?.store("vorArtworks")?.reloadList();
    });

    document.body.addEventListener("vor:reload-tree", () => {
        window.Alpine?.store("vorArtworks")?.reloadCollectionTree();
    });

    document.body.addEventListener("vor:close-modal", () => {
        window.Alpine?.store("vorArtworks")?.closeModal();
    });

    document.body.addEventListener("vor:collection-deleted", (event) => {
        const id = event.detail?.value ?? event.detail;
        window.Alpine?.store("vorArtworks")?.onCollectionDeleted(id);
    });

    document.body.addEventListener("vor:collection-renamed", (event) => {
        const payload = event.detail?.value ?? event.detail;
        const store = window.Alpine?.store("vorArtworks");
        if (!store || !payload) {
            return;
        }
        if (String(store.collectionId) === String(payload.id)) {
            store.collectionName = payload.name || store.collectionName;
        }
        store.collectionPath = (store.collectionPath || []).map((part) => (
            String(part.id) === String(payload.id)
                ? { ...part, name: payload.name || part.name }
                : part
        ));
    });

    document.addEventListener("contextmenu", (event) => {
        const store = window.Alpine?.store("vorArtworks");
        if (!store || !document.getElementById("vor-artworks-opts")) {
            return;
        }
        const collectionItem = event.target.closest(".collection-item");
        if (collectionItem) {
            event.preventDefault();
            store.openCollectionMenu(event, collectionItem);
            return;
        }
        const artwork = event.target.closest(".artwork-row, .artwork-tile");
        if (artwork) {
            event.preventDefault();
            store.openArtworkMenu(event, artwork.closest(".artwork-item"));
        }
    });

    document.addEventListener("pointermove", (event) => {
        const store = window.Alpine?.store("vorArtworks");
        if (store?._artworkDragging || store?.collectionDragging) {
            store.highlightCollectionAtPoint(event.clientX, event.clientY);
        }
    });

    document.addEventListener("click", (event) => {
        const store = window.Alpine?.store("vorArtworks");
        if (!store) {
            return;
        }
        const sidebar = document.getElementById("sidebar-collections-list");
        const toggle = event.target.closest(".collection-toggle");
        if (toggle && sidebar?.contains(toggle)) {
            store.closeMenu();
            const id = toggle.closest(".collection-tree-node")?.dataset.collectionId;
            if (id) {
                store.toggleCollectionExpanded(id);
            }
            return;
        }
        const collectionItem = event.target.closest(".collection-item");
        if (collectionItem && sidebar?.contains(collectionItem)) {
            store.closeMenu();
            store.selectCollectionFromEl(collectionItem);
            return;
        }
        if (!store.menu?.open) {
            return;
        }
        if (event.target.closest("#vor-context-menu")) {
            return;
        }
        store.closeMenu();
    });

    window.addEventListener("scroll", (event) => {
        const menu = document.getElementById("vor-context-menu");
        if (menu && (menu === event.target || menu.contains(event.target))) {
            return;
        }
        window.Alpine?.store("vorArtworks")?.closeMenu();
    }, true);

    (function initArtworkRowPreview() {
        const OFFSET = 14;
        const PAD = 12;
        const SHOW_DELAY = 180;
        let preview = null;
        let currentItem = null;
        let showTimer = 0;

        function ensurePreview() {
            if (preview) {
                return preview;
            }
            preview = document.createElement("div");
            preview.id = "artwork-row-preview";
            preview.className = "artwork-row-preview";
            preview.innerHTML = `
                <div class="artwork-row-preview-cover">
                    <img alt="">
                    <div class="artwork-row-preview-cover-empty"><i></i></div>
                </div>
                <div class="artwork-row-preview-body">
                    <div class="artwork-row-preview-title"></div>
                    <div class="artwork-row-preview-desc"></div>
                </div>
            `;
            document.body.appendChild(preview);
            return preview;
        }

        function hidePreview() {
            window.clearTimeout(showTimer);
            showTimer = 0;
            currentItem = null;
            if (preview) {
                preview.classList.remove("is-visible");
            }
        }

        function canShow(row) {
            if (!row) {
                return false;
            }
            if (document.body.classList.contains("vor-artworks-dragging")) {
                return false;
            }
            const list = row.closest(".artwork-list");
            if (!list || list.classList.contains("is-grid")) {
                return false;
            }
            if (window.Alpine?.store("vorArtworks")?.searchOpen) {
                return false;
            }
            if (window.Alpine?.store("vorArtworks")?.menu?.open) {
                return false;
            }
            return true;
        }

        function fillPreview(item) {
            const el = ensurePreview();
            const title = item.dataset.previewTitle || "";
            const cover = item.dataset.previewCover || "";
            el.querySelector(".artwork-row-preview-title").textContent = title;
            el.querySelector(".artwork-row-preview-desc").textContent =
                (item.dataset.previewDesc || "").replace(/\s+/g, " ").trim();
            const img = el.querySelector("img");
            img.alt = title;
            if (cover) {
                img.src = cover;
                el.classList.remove("is-empty");
            } else {
                img.removeAttribute("src");
                el.classList.add("is-empty");
                const icon = el.querySelector(".artwork-row-preview-cover-empty i");
                if (icon) {
                    icon.className = item.dataset.previewIcon || "";
                }
            }
        }

        function placePreview(clientX, clientY) {
            const el = ensurePreview();
            el.classList.add("is-visible");
            const width = el.offsetWidth;
            const height = el.offsetHeight;
            let x = clientX + OFFSET;
            let y = clientY + OFFSET;
            if (x + width > window.innerWidth - PAD) {
                x = clientX - width - OFFSET;
            }
            if (y + height > window.innerHeight - PAD) {
                y = clientY - height - OFFSET;
            }
            x = Math.max(PAD, x);
            y = Math.max(PAD, y);
            el.style.left = `${x}px`;
            el.style.top = `${y}px`;
        }

        document.addEventListener("pointermove", (event) => {
            const row = event.target.closest(".artwork-row");
            const item = row?.closest(".artwork-item");
            if (!canShow(row) || !item) {
                hidePreview();
                return;
            }
            if (currentItem !== item) {
                currentItem = item;
                fillPreview(item);
                window.clearTimeout(showTimer);
                if (preview?.classList.contains("is-visible")) {
                    placePreview(event.clientX, event.clientY);
                    return;
                }
                showTimer = window.setTimeout(() => {
                    if (currentItem === item) {
                        placePreview(event.clientX, event.clientY);
                    }
                }, SHOW_DELAY);
                return;
            }
            if (preview?.classList.contains("is-visible")) {
                placePreview(event.clientX, event.clientY);
            }
        });

        document.addEventListener("pointerdown", hidePreview);
        window.addEventListener("blur", hidePreview);
        window.addEventListener("scroll", hidePreview, true);
    })();

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
            if (hasContent("vor-modal")) {
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
