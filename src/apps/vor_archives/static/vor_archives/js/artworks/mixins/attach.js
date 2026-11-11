import { VorApi } from "@vor/artworks/api";

export function getAttachMixin({
  attachUrl = "",
} = {}) {
  return {
    attachUrl,
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
      const wId = this.workId || this.createdWorkId;
      if (!wId) return;
      this.saving = true;
      try {
        const data = await VorApi.attachWork(this.attachUrl, {
          work_type: this.createdWorkType || this.workType,
          work_id: wId,
          status: this.status || "planning",
          rating: this.rating || "",
          progress: this.progress || 0,
        });
        if (!data || !data.ok) {
          if (typeof this.onAttachError === "function") this.onAttachError();
          return;
        }
        if (typeof this.onAttachSuccess === "function") this.onAttachSuccess();
      } finally {
        this.saving = false;
      }
    }
  };
}
