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

    document.body.addEventListener("htmx:configRequest", (event) => {
        const token =
            document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
            getCookie("csrftoken");
        if (token) {
            event.detail.headers["X-CSRFToken"] = token;
        }
    });

    document.body.addEventListener("htmx:afterSwap", (event) => {
        const elt = event.detail.elt;
        const init = () => {
            if (window.Alpine && elt) {
                Alpine.initTree(elt);
            }
        };
        if (window.Alpine) {
            init();
        } else {
            document.addEventListener("alpine:init", init, { once: true });
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
        }));

        Alpine.data("vorAddOverlay", (opts = {}) => ({
            workType: opts.workType || "book",
            title: opts.title || "",
            selectedWorkId: null,
            filmType: "movie",
            setType(type) {
                this.workType = type;
                this.clearSelection();
                const suggestions = document.getElementById("work-suggestions");
                if (suggestions) {
                    suggestions.innerHTML = "";
                }
                if (this.title.trim()) {
                    this.$nextTick(() => {
                        const input = document.getElementById("add-title-input");
                        if (input) {
                            htmx.trigger(input, "input");
                        }
                    });
                }
            },
            selectWork(id) {
                this.selectedWorkId = Number(id);
            },
            clearSelection() {
                this.selectedWorkId = null;
                const preview = document.getElementById("add-preview");
                if (preview) {
                    preview.innerHTML = "";
                }
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
