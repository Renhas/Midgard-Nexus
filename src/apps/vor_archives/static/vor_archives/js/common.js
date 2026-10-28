(function () {
    window.getCookie = function (name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    };

    window.hasContent = function (id) {
        const el = document.getElementById(id);
        return Boolean(el && el.innerHTML.trim());
    };

    window.syncPageScrollLock = function () {
        const locked = window.hasContent("vor-overlay")
            || Boolean(window.Alpine?.store("vorArtworks")?.searchOpen);
        document.documentElement.classList.toggle("vor-scroll-lock", locked);
    };

    window.overlayAlpine = function () {
        const el = document.querySelector("#vor-overlay .vor-overlay");
        return el && window.Alpine ? Alpine.$data(el) : null;
    };

    window.cropCoverFile = function (file) {
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
    };

    window.DATE_MONTHS_FULL = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ];
    window.DATE_MONTHS_SHORT = [
        "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
        "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек",
    ];

    window.toIsoDate = function (date) {
        return [
            date.getFullYear(),
            String(date.getMonth() + 1).padStart(2, "0"),
            String(date.getDate()).padStart(2, "0"),
        ].join("-");
    };

    window.wheelDirection = function (event) {
        return event.deltaY < 0 ? 1 : event.deltaY > 0 ? -1 : 0;
    };

    window.datePickerApi = function () {
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
                return `${window.DATE_MONTHS_FULL[cursor.getMonth()]} ${cursor.getFullYear()}`;
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
                    const iso = window.toIsoDate(date);
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
                return window.DATE_MONTHS_SHORT;
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
                this.setReleaseDate(window.toIsoDate(new Date()));
            },
            onNumberWheel(event, field, min = 1, max = null) {
                const direction = window.wheelDirection(event);
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
                const direction = window.wheelDirection(event);
                if (!direction) {
                    return;
                }
                const options = [""].concat((this.ageChoices || []).map((item) => item.value));
                const index = Math.max(0, options.indexOf(this.ageRating || ""));
                const next = Math.max(0, Math.min(options.length - 1, index + direction));
                this.ageRating = options[next];
            },
            onFilmTypeWheel(event) {
                const direction = window.wheelDirection(event);
                if (!direction) {
                    return;
                }
                const options = ["movie", "tv_show"];
                const index = Math.max(0, options.indexOf(this.filmType || "movie"));
                const next = Math.max(0, Math.min(options.length - 1, index + direction));
                this.filmType = options[next];
            },
        };
    };

    window.overlayRequestPath = function (event) {
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
    };

    window.pushOverlayHistory = function (event) {
        if (window.__vorRestoringOverlay) {
            window.__vorRestoringOverlay = false;
            return;
        }
        if (!window.hasContent("vor-overlay")) {
            return;
        }
        const overlayUrl = window.overlayRequestPath(event);
        if (!overlayUrl || history.state?.vorOverlay === overlayUrl) {
            return;
        }
        history.pushState({ vorOverlay: overlayUrl }, "", window.location.href);
    };

    window.restoreOverlay = function (overlayUrl) {
        window.__vorRestoringOverlay = true;
        htmx.ajax("GET", overlayUrl, {
            target: "#vor-overlay",
            swap: "innerHTML",
        });
    };

    window.leaveOverlayOnCurrentPage = function () {
        if (!window.hasContent("vor-overlay")) {
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
        const data = window.overlayAlpine();
        if (data?.editing) {
            return data.tryLeave(proceed);
        }
        proceed();
        return true;
    };

    window.isSamePageLink = function (anchor) {
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
    };

    window.SIDEBAR_STORAGE_KEY = "vor.artworks.sidebar";
    window.ALL_WORK_TYPES = ["book", "film", "game"];
    window.FILTER_KEYS = [
        "status", "age_rating", "tags", "genre_book", "genre_film", "genre_game", "platform",
    ];

    window.mergeFilterSelection = function (allIds, savedSelected, savedKnown) {
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
    };

    window.addEventListener("popstate", (event) => {
        const overlayUrl = event.state && event.state.vorOverlay;
        if (overlayUrl) {
            window.restoreOverlay(overlayUrl);
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
            if (!anchor || !window.hasContent("vor-overlay")) {
                return;
            }
            if (window.isSamePageLink(anchor)) {
                event.preventDefault();
                window.leaveOverlayOnCurrentPage();
                return;
            }
            const data = window.overlayAlpine();
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
            window.getCookie("csrftoken");
        if (token) {
            event.detail.headers["X-CSRFToken"] = token;
        }
    });

    document.body.addEventListener("htmx:afterSwap", (event) => {
        const el = event.detail.elt;
        if (el?.id === "vor-overlay") {
            window.pushOverlayHistory(event);
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
        window.syncPageScrollLock();
    });

    const overlayEl = document.getElementById("vor-overlay");
    if (overlayEl) {
        new MutationObserver(window.syncPageScrollLock).observe(overlayEl, { childList: true });
    }

    document.addEventListener("keydown", (event) => {
        if (!(event.ctrlKey || event.metaKey) || event.code !== "KeyF") {
            return;
        }
        if (!document.getElementById("vor-artworks-opts")) {
            return;
        }
        if (window.hasContent("vor-overlay")) {
            return;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        window.Alpine?.store("vorArtworks")?.openSearch();
    }, true);
})();
