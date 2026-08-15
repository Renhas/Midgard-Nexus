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
        if (history.state?.vorOverlay) {
            history.pushState({}, "", window.location.href);
        }
        const el = document.getElementById("vor-overlay");
        if (el) {
            el.innerHTML = "";
        }
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
            if (!anchor || !isSamePageLink(anchor) || !hasContent("vor-overlay")) {
                return;
            }
            event.preventDefault();
            leaveOverlayOnCurrentPage();
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

    document.body.addEventListener("htmx:afterSwap", (event) => {
        if (event.detail.elt?.id === "vor-overlay") {
            pushOverlayHistory(event);
        }
    });

    document.addEventListener("alpine:init", () => {
        Alpine.store("vorArtworks", {
            deleteMode: false,
            selectedIds: [],

            enterDeleteMode() {
                this.deleteMode = true;
                this.selectedIds = [];
            },
            exitDeleteMode() {
                this.deleteMode = false;
                this.selectedIds = [];
            },
            toggleSelected(id) {
                id = Number(id);
                const index = this.selectedIds.indexOf(id);
                if (index > -1) {
                    this.selectedIds.splice(index, 1);
                } else {
                    this.selectedIds.push(id);
                }
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

        Alpine.data("vorDetailOverlay", (opts = {}) => ({
            editing: Boolean(opts.editing),
            globalEdit: Boolean(opts.globalEdit),
            filmType: opts.filmType || "movie",
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
            },
            saveField(field, value) {
                if (!this.quickUrl) {
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
                if (!this.listUrl) {
                    return;
                }
                htmx.ajax("GET", this.listUrl, {
                    target: "#artwork-list",
                    swap: "outerHTML",
                });
            },
        }));

        Alpine.data("vorChipOverflow", () => ({
            hiddenCount: 0,
            visibleCount: 0,
            popupOpen: false,
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
            workTitle: opts.workTitle || "",
            selectedWorkId: null,
            alreadyOwned: false,
            filmType: "movie",
            setType(type) {
                this.workType = type;
                this.clearSelection();
                this.refreshSearch();
            },
            onTitleInput() {
                this.clearSelection();
            },
            selectWork(id) {
                this.selectedWorkId = Number(id);
                this.clearSuggestions();
            },
            clearSelection() {
                this.selectedWorkId = null;
                this.alreadyOwned = false;
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
                this.clearSuggestions();
                const query = String(this.workTitle || "").trim();
                if (!query) {
                    return;
                }
                const input = document.getElementById("add-title-input");
                const url = input?.dataset.searchUrl;
                if (!url) {
                    return;
                }
                const params = new URLSearchParams({
                    work_type: this.workType,
                    q: query,
                });
                htmx.ajax("GET", `${url}?${params.toString()}`, {
                    target: "#work-suggestions",
                    swap: "innerHTML",
                });
            },
        }));
    });

    document.addEventListener("keydown", (event) => {
        const store = window.Alpine?.store("vorArtworks");
        if (!store) {
            return;
        }
        if (event.key === "Escape") {
            if (hasContent("vor-modal")) {
                store.closeModal();
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
            if (!item || event.target.closest(".artwork-row-delete")) {
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
})();
