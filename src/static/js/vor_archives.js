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
                    htmx.ajax("GET", `/library/works/${item.type_key}/${item.work_id}/`, {
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
                if (!this.listUrl) {
                    return;
                }
                htmx.ajax("GET", this.listUrl, {
                    target: "#artwork-list",
                    swap: "outerHTML",
                });
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
                    htmx.ajax("GET", `/library/works/${this.workType}/${this.workId}/`, {
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
                if (!this.listUrl) {
                    return;
                }
                htmx.ajax("GET", this.listUrl, {
                    target: "#artwork-list",
                    swap: "outerHTML",
                });
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
