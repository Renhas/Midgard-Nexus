import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { getOverlayLifecycleMixin } from "@vor/artworks/mixins/overlay_lifecycle";
import { getDatePickerMixin } from "@vor/artworks/mixins/datepicker";
import { getCoverMixin, getStatusMixin, getRatingMixin, getProgressMixin, getRelationsMixin, getAttachMixin } from "@vor/artworks/overlay_mixins";
import { getAgePickerMixin } from "@vor/artworks/mixins/age_picker";
import { getNumberWheelMixin } from "@vor/artworks/mixins/number_wheel";
import { getAttributeMixin } from "@vor/artworks/mixins/attributes";
import { getWorkFieldsMixin } from "@vor/artworks/mixins/work_fields";
import { wheelDirection } from "@vor/shared/pure/wheel";
import { getValidationMixin } from "@vor/artworks/mixins/validation";
import { VorApi } from "@vor/artworks/api";

document.addEventListener("alpine:init", () => {
  getAlpine().data("vorAddOverlay", (opts = {}) => ({
    saveUrl: opts.saveUrl || "",
    searchUrl: opts.searchUrl || "",
    previewUrl: opts.previewUrl || "",
    relationSearchUrl: opts.relationSearchUrl || "",
    selectedWorkId: null,
    createdWorkId: null,
    createdWorkType: "",
    justCreated: false,
    phase: "form",
    saving: false,
    errors: {},
    formError: "",
    doneMessage: "",
    ...getDatePickerMixin({ dateCursor: new Date() }),
    searchTimer: null,
    ...getCoverMixin(),
    ...getStatusMixin({ choices: opts.statusChoices }),
    ...getRatingMixin(),
    ...getProgressMixin(),
    ...getRelationsMixin({ relationTypes: opts.relationTypes }),
    ...getAttachMixin({ attachUrl: opts.attachUrl }),
    ...getWorkFieldsMixin({ workType: opts.workType || "book" }),
    ...getAgePickerMixin({ ageChoices: opts.ageChoices }),
    ...getValidationMixin({ requiredFieldsByType: opts.requiredFields }),
    ...getNumberWheelMixin(),
    ...getAttributeMixin({ catalogs: opts.catalogs }),
    ...getOverlayLifecycleMixin(),
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
      const currentTitleErrors = this.errors.title || [];
      if (currentTitleErrors.length === 1 && currentTitleErrors[0]?.persistent) {
        const { title, ...rest } = this.errors;
        this.errors = rest;
      }
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
    onSuggestionsLoaded(owned) {
      const alreadyOwnedMessage = "Это произведение уже есть в вашем списке";
      if (owned) {
        this.errors = {
          ...this.errors,
          title: [{ message: alreadyOwnedMessage, persistent: true }],
        };
        return;
      }
      const currentTitleErrors = this.errors.title || [];
      if (currentTitleErrors.length === 1 && currentTitleErrors[0]?.persistent) {
        const { title, ...rest } = this.errors;
        this.errors = rest;
      }
    },
    appendIds(body, name, items) {
      (items || []).forEach((item) => body.append(name, String(item.id)));
    },
    async saveWork() {
      if (this.saving) {
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
      this.errors = {};
      try {
        const data = await VorApi.saveWork(this.saveUrl, body);
        if (!data || !data.ok) {
          this.errors = (data && data.errors) || {};
          if (!data || !Object.keys(this.errors).length) {
            this.formError = "Не удалось сохранить произведение";
          }
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
    finishCreate() {
      this.doneMessage = "Произведение успешно сохранено в базу данных.";
      this.phase = "done";
      this.refreshList();
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
        this.finishCreate();
      }
    },
    goToList() {
      this.refreshList();
      this.closeOverlay();
    },
    resetForm() {
      this.resetWorkFields();
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
      this.doneMessage = "";
      this.resetAttachFields();
      this.phase = "form";
    },
    onAttachSuccess() {
      this.doneMessage = this.justCreated
        ? "Произведение создано и добавлено в ваш список."
        : "Произведение добавлено в ваш список.";
      this.phase = "done";
      this.refreshList();
    },
    onAttachError() {
      this.formError = "Не удалось добавить произведение в список";
    },
    onFilmTypeWheel(event) {
      const direction = wheelDirection(event.deltaY);
      if (!direction) {
        return;
      }
      const options = ["movie", "tv_show"];
      const index = Math.max(0, options.indexOf(this.filmType || "movie"));
      const next = Math.max(0, Math.min(options.length - 1, index + direction));
      this.filmType = options[next];
    },
  }));
});
