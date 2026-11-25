import { VorApi } from "@vor/artworks/api";
import { getDomainConfig } from "@vor/shared/domain";

export function getAttachMixin({ attachUrl = "" } = {}) {
  const defaultStatus = () => getDomainConfig().statuses?.default || "planning";
  return {
    attachUrl,
    resetAttachFields() {
      this.status = defaultStatus();
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
          status: this.status || defaultStatus(),
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
    },
  };
}
