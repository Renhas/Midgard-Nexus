import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { getOverlayLifecycleMixin } from "@vor/artworks/mixins/overlay_lifecycle";
import { getDatePickerMixin } from "@vor/artworks/mixins/datepicker";
import { getCoverMixin, getStatusMixin, getRatingMixin, getProgressMixin, getRelationsMixin, getAttachMixin } from "@vor/artworks/overlay_mixins";
import { getAgePickerMixin } from "@vor/artworks/mixins/age_picker";
import { getNumberWheelMixin } from "@vor/artworks/mixins/number_wheel";
import { getAttributeMixin } from "@vor/artworks/mixins/attributes";
import { getWorkFieldsMixin } from "@vor/artworks/mixins/work_fields";
import { serializeDraft, parseDraft, dirtyChanges as dirtyChangesPure } from "@vor/artworks/pure/draft";
import {
  captureQuickState as captureQuickStatePure,
  restoreQuickState as restoreQuickStatePure,
  applyQuickResult as applyQuickResultPure,
} from "@vor/artworks/pure/quick_state";
import { VorApi } from "@vor/artworks/api";

const DRAFT_FIELD_LABELS = {
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

document.addEventListener("alpine:init", () => {
  getAlpine().data("vorDetailOverlay", (opts = {}) => ({
    editing: Boolean(opts.editing),
    workId: opts.workId || null,
    relationSearchUrl: opts.relationSearchUrl || "",
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
    workUrl: opts.workUrl || "",
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
    ...getAttachMixin({ attachUrl: opts.attachUrl }),
    ...getWorkFieldsMixin(opts),
    ...getAgePickerMixin({ ageChoices: opts.ageChoices }),
    ...getNumberWheelMixin(),
    ...getAttributeMixin({ catalogs: { [opts.workType]: opts.catalog || {} } }),
    ...getOverlayLifecycleMixin(),
    init() {
      this.snapshot = this.buildSnapshot();
      this.serverQuickState = captureQuickStatePure(this);
    },
    buildSnapshot() {
      return serializeDraft({
        ...this.workFieldsSnapshot(),
        relations: this.relations,
        coverPreview: this.coverPreview,
        coverCleared: this.coverCleared,
        coverName: this.coverFile?.name || "",
      });
    },
    startEdit() {
      this.editing = true;
      this.coverWarning = "";
      this.snapshot = this.buildSnapshot();
    },
    cancelEdit() {
      this.leaveOr(() => this.revertEdit());
    },
    revertEdit() {
      const data = parseDraft(this.snapshot);
      this.applyWorkFields(data);
      this.relations = data.relations || [];
      this.resetCover(data.coverPreview || "");
      this.relAdding = false;
      this.editing = false;
      this.leaveConfirmOpen = false;
    },
    dirtyChanges() {
      if (!this.editing) {
        return [];
      }
      const before = parseDraft(this.snapshot);
      const after = parseDraft(this.buildSnapshot());
      return dirtyChangesPure(
        before,
        after,
        DRAFT_FIELD_LABELS,
        Boolean(this.coverFile || this.coverCleared),
      );
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
      tipEl.style.setProperty("--tip-left", `${rect.left}px`);
      tipEl.style.setProperty("--tip-top", `${rect.bottom + 6}px`);
      tipEl.style.setProperty("--tip-shift-y", "0px");
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
    async saveField(field, value) {
      if (!this.quickUrl || this.attachOpen) return;
      const seq = ++this._quickSeq;
      const data = await VorApi.quickUpdate(this.quickUrl, field, value);
      if (seq !== this._quickSeq) return;
      if (!data || typeof data !== "object") {
        restoreQuickStatePure(this, this.serverQuickState);
        return;
      }
      applyQuickResultPure(this, data);
      this.serverQuickState = captureQuickStatePure(this);
      this.refreshList();
    },
    startAttach() {
      this.resetAttachFields();
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
