document.addEventListener("alpine:init", () => {
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
    ...window.datePickerApi(),
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
    ...window.getCoverHelpers(),
    ...window.getStatusHelpers(),
    ...window.getRatingHelpers(),
    ...window.getProgressHelpers(),
    ...window.getRelationsHelpers(),
    ...window.getAttachHelpers(),
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
      return window.getCsrfToken();
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
      window.Alpine?.store("vorArtworks")?.reloadList();
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
  }));
});
