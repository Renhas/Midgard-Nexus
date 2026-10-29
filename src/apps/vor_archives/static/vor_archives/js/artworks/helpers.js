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
})();
