import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { closeOverlay as closeOverlayImpl } from "@vor/shared/overlay_lifecycle";
import { getDatePickerMixin } from "@vor/artworks/mixins/datepicker";
import { getCoverMixin, getStatusMixin, getRatingMixin, getProgressMixin, getRelationsMixin, getAttachMixin } from "@vor/artworks/overlay_mixins";
import { VorApi } from "@vor/artworks/api";

document.addEventListener("alpine:init", () => {
  getAlpine().data("vorDetailOverlay", (opts = {}) => ({
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
    authors: opts.authors || [],
    genres: opts.genres || [],
    tags: opts.tags || [],
    platforms: opts.platforms || [],
    catalog: opts.catalog || {},
    ageChoices: opts.ageChoices || [],
    saveUrl: opts.saveUrl || "",
    relationSearchUrl: opts.relationSearchUrl || "",
    pickerKind: null,
    pickerQuery: "",
    pickerSelected: {},
    ageOpen: false,
    ...getDatePickerMixin({
      dateCursor: opts.releaseDate ? new Date(`${opts.releaseDate}T00:00:00`) : new Date(),
    }),
    linkOpen: false,
    leaveConfirmOpen: false,
    attachOpen: false,
    saving: false,
    leaveChanges: [],
    leaveAction: null,
    snapshot: "",
    owned: Boolean(opts.owned),
    ownedPlatformIds: opts.ownedPlatformIds || [],
    isHidden: Boolean(opts.isHidden),
    timesCompleted: Number(opts.timesCompleted || 0),
    lastCompletedDate: opts.lastCompletedDate || "",
    counterEditing: false,
    counterHover: false,
    counterDraft: "",
    quickUrl: opts.quickUrl || "",
    _quickSeq: 0,
    serverQuickState: null,
    listUrl: opts.listUrl || "",
    workUrl: opts.workUrl || "",
    attachUrl: opts.attachUrl || "",
    ...getCoverMixin({ coverPreview: opts.coverUrl || "" }),
    ...getStatusMixin({ status: opts.status || "planning", choices: opts.statusChoices }),
    ...getRatingMixin({ rating: Number(opts.rating || 0) }),
    ...getProgressMixin({
      progress: Number(opts.progress || 0),
      progressMax: opts.progressMax == null ? null : Number(opts.progressMax),
      progressUnit: opts.progressUnit || "",
      progressStep: Number(opts.progressStep || 1),
    }),
    ...getRelationsMixin({
      relations: opts.relations,
      relationTypes: opts.relationTypes,
    }),
    ...getAttachMixin(),
    init() {
      this.snapshot = this.serializeDraft();
      this.serverQuickState = this.captureQuickState();
    },
    closeOverlay() {
      return closeOverlayImpl();
    },
    captureQuickState() {
      return {
        status: this.status,
        rating: this.rating,
        progress: this.progress,
        isHidden: this.isHidden,
        timesCompleted: this.timesCompleted,
        ownedPlatformIds: [...this.ownedPlatformIds],
        lastCompletedDate: this.lastCompletedDate,
      };
    },
    restoreQuickState(snap) {
      if (!snap) {
        return;
      }
      this.status = snap.status;
      this.rating = snap.rating;
      this.progress = snap.progress;
      this.isHidden = snap.isHidden;
      this.timesCompleted = snap.timesCompleted;
      this.ownedPlatformIds = snap.ownedPlatformIds;
      this.lastCompletedDate = snap.lastCompletedDate;
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
    openRelated(item) {
      this.leaveOr(() => {
        htmx.ajax("GET", item.url, {
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
    async saveField(field, value) {
      if (!this.quickUrl || this.attachOpen) return;
      const seq = ++this._quickSeq;
      const data = await VorApi.quickUpdate(this.quickUrl, field, value);
      if (seq !== this._quickSeq) return;
      if (!data || typeof data !== "object") {
        this.restoreQuickState(this.serverQuickState);
        return;
      }
      this.applyQuickResult(data);
      this.serverQuickState = this.captureQuickState();
      this.refreshList();
    },
    refreshList() {
      document.body.dispatchEvent(new CustomEvent("vor:reload-list"));
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
    onAttachSuccess() {
      this.attachOpen = false;
      this.refreshList();
      htmx.ajax("GET", this.workUrl, {
        target: "#vor-overlay",
        swap: "innerHTML",
      });
    },
    onAttachError() {
      // В оверлее ошибка сейчас обрабатывается молча
    },
  }));
});
