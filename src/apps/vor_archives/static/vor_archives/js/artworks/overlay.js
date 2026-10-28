document.addEventListener("alpine:init", () => {
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
        ...window.datePickerApi(),
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
            const result = await window.cropCoverFile(file);
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
                || window.getCookie("csrftoken");
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
});
