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
})();
