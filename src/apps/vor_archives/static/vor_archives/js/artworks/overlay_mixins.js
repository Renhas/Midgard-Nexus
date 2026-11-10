import { VorApi } from "@vor/artworks/api";
import { cropCoverFile } from "@vor/shared/cover";
import {
  displayRating as pureDisplayRating,
  ratingLabel as pureRatingLabel,
  starState as pureStarState,
} from "@vor/artworks/pure/rating";
import {
  progressValueLabel as pureProgressValueLabel,
  progressSuffix as pureProgressSuffix,
  progressCh as pureProgressCh,
  clampProgress as pureClampProgress,
  parseProgressDraft as pureParseProgressDraft,
} from "@vor/artworks/pure/progress";
import {
  allowedRelationTypes as pureAllowedRelationTypes,
  relationKey as pureRelationKey,
  relationLabelFor as pureRelationLabelFor,
} from "@vor/artworks/pure/relations";

export function getCoverMixin() {
  return {
    async onCoverSelected(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) {
        return;
      }
      const result = await cropCoverFile(file);
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

export function getStatusMixin() {
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

export function getRatingMixin() {
  return {
    displayRating() {
      return pureDisplayRating(this.rating, this.hoverRating);
    },
    ratingLabel() {
      return pureRatingLabel(this.displayRating());
    },
    starState(star) {
      return pureStarState(this.displayRating(), star);
    },
    setRating(value) {
      this.rating = this.rating === value ? 0 : value;
      if (typeof this.saveField === "function") {
        this.saveField("rating", this.rating);
      }
    }
  };
};

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
};

export function getRelationsMixin() {
  return {
    allowedRelationTypes(otherType) {
      return pureAllowedRelationTypes(this.relationTypes, otherType, this.workType);
    },
    relationKey(item) {
      return pureRelationKey(item);
    },
    relationLabelFor(type, direction) {
      return pureRelationLabelFor(this.relationTypes, type, direction);
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
    async searchRelatedWorks() {
      const query = String(this.relQuery || "").trim();
      if (!query || !this.relationSearchUrl) {
        this.relResults = [];
        return;
      }
      const wId = this.workId || this.createdWorkId || "";
      const data = await VorApi.searchRelatedWorks(this.relationSearchUrl, {
        q: query,
        exclude_type: this.workType,
        exclude_id: String(wId),
      });
      const taken = new Set(
        this.relations.map((item) => `${item.type_key}-${item.work_id}`)
      );
      this.relResults = (data?.results || []).filter(
        (item) => !taken.has(`${item.type_key}-${item.work_id}`)
      );
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

export function getAttachMixin() {
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
};
