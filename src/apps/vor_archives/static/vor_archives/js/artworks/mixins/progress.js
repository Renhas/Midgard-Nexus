import {
  progressValueLabel as pureProgressValueLabel,
  progressSuffix as pureProgressSuffix,
  progressCh as pureProgressCh,
  clampProgress as pureClampProgress,
  parseProgressDraft as pureParseProgressDraft,
} from "@vor/artworks/pure/progress";

export function getProgressMixin() {
  return {
    progressValueLabel() {
      return pureProgressValueLabel(this.progress);
    },
    progressSuffix() {
      return pureProgressSuffix(this.progressMax, this.progressUnit);
    },
    progressCh() {
      return pureProgressCh(this.progressMax);
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
      const parsed = pureParseProgressDraft(this.progressDraft);
      if (parsed == null) return;
      this.applyProgress(parsed);
    },
    nudgeProgress(direction) {
      this.applyProgress(this.progress + direction * this.progressStep);
    },
    applyProgress(value) {
      this.progress = pureClampProgress(value, this.progressMax);
      if (this.progressMax != null && this.progress >= this.progressMax) {
        this.status = "completed";
      }
      if (typeof this.saveField === "function") {
        this.saveField("progress", this.progress);
      }
    },
    clampProgress(value) {
      return pureClampProgress(value, this.progressMax);
    }
  };
}
