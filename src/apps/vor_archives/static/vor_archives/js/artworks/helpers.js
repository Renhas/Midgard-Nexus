(function () {
    window.getCoverHelpers = function () {
        return {
            async onCoverSelected(event) {
                const file = event.target.files && event.target.files[0];
                if (!file) {
                    return;
                }
                const result = await window.cropCoverFile(file);
                this.coverFile = result.file;
                if ("coverCleared" in this) {
                    this.coverCleared = false;
                }
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
                if ("coverCleared" in this) {
                    this.coverCleared = true;
                }
                this.coverWarning = "";
                if (this.$refs.coverInput) {
                    this.$refs.coverInput.value = "";
                }
            }
        };
    };
    window.getStatusHelpers = function () {
        return {
            statusLabel() {
                const found = this.statusChoices.find((item) => item.value === this.status);
                return found ? found.label : (this.status || "planning");
            },
            setStatus(value) {
                this.statusOpen = false;
                if (this.status === value) return;
                this.status = value;
                if (value === "completed" && this.progressMax != null) {
                    this.progress = this.progressMax;
                }
                if (value === "in_progress") {
                    this.progress = 0;
                }
                if (typeof this.saveField === "function") {
                    this.saveField("status", value);
                }
            }
        };
    };

    window.getRatingHelpers = function () {
        return {
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
                if (shown >= fullAt) return "is-full";
                if (shown === fullAt - 1) return "is-half";
                return "is-empty";
            },
            setRating(value) {
                this.rating = this.rating === value ? 0 : value;
                if (typeof this.saveField === "function") {
                    this.saveField("rating", this.rating);
                }
            }
        };
    };

    window.getProgressHelpers = function () {
        return {
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
                if (!this.progressEditing) return;
                this.progressEditing = false;
                this.progressHover = false;
                const parsed = Number(String(this.progressDraft).replace(",", "."));
                if (Number.isNaN(parsed)) return;
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
                if (typeof this.saveField === "function") {
                    this.saveField("progress", this.progress);
                }
            },
            clampProgress(value) {
                let next = Math.max(0, value);
                if (this.progressMax != null) {
                    next = Math.min(this.progressMax, next);
                }
                return Math.round(next * 10) / 10;
            }
        };
    };

    window.getRelationsHelpers = function () {
        return {
            allowedRelationTypes(otherType) {
                return this.relationTypes.filter((opt) => {
                    if (opt.value === "other") return true;
                    if (opt.value === "adaptation") return otherType && otherType !== this.workType;
                    return otherType === this.workType;
                });
            },
            relationKey(item) {
                return `${item.id || "new"}-${item.type_key}-${item.work_id}`;
            },
            relationLabelFor(type, direction) {
                const found = this.relationTypes.find((item) => item.value === type);
                if (type === "sequel") return direction === "in" ? "Предыстория" : "Продолжение";
                if (type === "spin_off") return direction === "in" ? "Оригинал" : "Спин-офф";
                if (type === "adaptation") return direction === "in" ? "Первоисточник" : "Адаптация";
                if (type === "remake") return direction === "in" ? "Оригинал" : "Ремейк";
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
                // Fallback на createdWorkId для контекста добавления
                const wId = this.workId || this.createdWorkId || "";
                const params = new URLSearchParams({
                    q: query,
                    exclude_type: this.workType,
                    exclude_id: String(wId),
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
                if (!this.relPick) return;
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
            }
        };
    };

    window.getAttachHelpers = function () {
        return {
            resetAttachFields() {
                this.status = "planning";
                this.statusOpen = false;
                this.rating = 0;
                this.hoverRating = 0;
                this.progress = 0;
                this.progressEditing = false;
                this.progressHover = false;
            },
            async saveAttach() {
                if (this.saving || !this.attachUrl) return;

                // Fallback на createdWorkId для контекста добавления
                const wId = this.workId || this.createdWorkId;
                if (!wId) return;

                const body = new URLSearchParams({
                    work_type: this.createdWorkType || this.workType, // Приоритет для add.js
                    work_id: String(wId),
                    status: this.status || "planning",
                    rating: this.rating ? String(this.rating) : "",
                    progress: String(this.progress || 0),
                });

                this.saving = true;
                try {
                    const response = await fetch(this.attachUrl, {
                        method: "POST",
                        headers: {
                            ...window.getCsrfHeaders(),
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body,
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || !data.ok) {
                        if (typeof this.onAttachError === "function") this.onAttachError();
                        return;
                    }
                    if (typeof this.onAttachSuccess === "function") this.onAttachSuccess();
                } catch (error) {
                    if (typeof this.onAttachError === "function") this.onAttachError();
                } finally {
                    this.saving = false;
                }
            }
        };
    };
})();
