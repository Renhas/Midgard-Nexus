import { htmx } from "@lib/htmx";
import { getAlpine } from "@lib/alpine";
import { mergeFilterSelection } from "@vor/artworks/pure/filter_selection";

const ALL_WORK_TYPES = ["book", "film", "game"];
const FILTER_KEYS = [
  "status", "age_rating", "tags", "genre_book", "genre_film", "genre_game", "platform",
];
const SIDEBAR_STORAGE_KEY = "vor.artworks.sidebar";

export const filtersMixin = {
  workTypes: [...ALL_WORK_TYPES],
  showHidden: true,
  viewMode: "list",
  sortField: "custom",
  sortAsc: true,
  filters: {
    status: [], age_rating: [], tags: [],
    genre_book: [], genre_film: [], genre_game: [], platform: [],
  },
  filterCatalog: {
    status: [], age_rating: [], tags: [],
    genre_book: [], genre_film: [], genre_game: [], platform: [],
  },
  listUrl: "",

  get listTitle() {
    return this.collectionId ? (this.collectionName || "Коллекция") : "Медиатека";
  },
  restoreSidebar() {
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem(SIDEBAR_STORAGE_KEY) || "null");
    } catch (error) {
      saved = null;
    }
    if (!saved) {
      return;
    }
    if (Array.isArray(saved.workTypes)) {
      this.workTypes = saved.workTypes.filter((type) => ALL_WORK_TYPES.includes(type));
    }
    if (typeof saved.showHidden === "boolean") {
      this.showHidden = saved.showHidden;
    }
    if (saved.viewMode === "list" || saved.viewMode === "grid") {
      this.viewMode = saved.viewMode;
    }
    if (saved.sortField) {
      this.sortField = saved.sortField;
    }
    if (typeof saved.sortAsc === "boolean") {
      this.sortAsc = saved.sortAsc;
    }
    FILTER_KEYS.forEach((key) => {
      this.filters[key] = mergeFilterSelection(
        this.filterCatalog[key],
        saved.filters?.[key],
        saved.known?.[key]
      );
    });
  },
  persistSidebar() {
    const known = {};
    const filters = {};
    FILTER_KEYS.forEach((key) => {
      known[key] = [...(this.filterCatalog[key] || [])];
      filters[key] = [...(this.filters[key] || [])];
    });
    localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify({
      workTypes: [...this.workTypes],
      showHidden: this.showHidden,
      viewMode: this.viewMode,
      sortField: this.sortField,
      sortAsc: this.sortAsc,
      filters,
      known,
    }));
  },
  resetFilters(reload = true) {
    FILTER_KEYS.forEach((key) => {
      this.filters[key] = [...(this.filterCatalog[key] || [])];
    });
    if (reload) {
      this.persistSidebar();
      this.reloadList();
    }
  },
  setShowHidden(value) {
    this.showHidden = Boolean(value);
    this.persistSidebar();
    this.reloadList();
  },
  toggleType(type) {
    const index = this.workTypes.indexOf(type);
    if (index > -1) {
      this.workTypes.splice(index, 1);
    } else {
      this.workTypes.push(type);
    }
    this.persistSidebar();
    this.reloadList();
  },
  setViewMode(mode) {
    if (this.viewMode === mode) {
      return;
    }
    this.viewMode = mode;
    this.persistSidebar();
    this.applyListState();
  },
  setSortField(field) {
    this.sortField = field;
    this.persistSidebar();
    this.applyListState();
    this.reloadList();
  },
  toggleSortDir() {
    this.sortAsc = !this.sortAsc;
    this.persistSidebar();
    this.applyListState();
    this.reloadList();
  },
  toggleFilter(name, value) {
    const list = this.filters[name] || [];
    const index = list.map(String).indexOf(String(value));
    if (index > -1) {
      list.splice(index, 1);
    } else {
      list.push(value);
    }
    this.filters[name] = list;
    this.persistSidebar();
    this.reloadList();
  },
  isFilterOn(name, value) {
    return (this.filters[name] || []).map(String).includes(String(value));
  },
  clearFilter(name) {
    this.filters[name] = [];
    this.persistSidebar();
    this.reloadList();
  },
  listQuery() {
    const params = new URLSearchParams();
    if (this.workTypes.length) {
      this.workTypes.forEach((type) => params.append("types", type));
    } else {
      params.append("types", "");
    }
    params.set("sort", this.sortField);
    params.set("dir", this.sortAsc ? "asc" : "desc");
    params.set("hidden", this.showHidden ? "1" : "0");
    if (this.collectionId) {
      params.set("collection", String(this.collectionId));
    }
    FILTER_KEYS.forEach((name) => {
      (this.filters[name] || []).forEach((value) => params.append(name, value));
    });
    return params;
  },
  reloadList() {
    if (!this.listUrl) {
      return;
    }
    this.closeMenu();
    this._reloadSeq = (this._reloadSeq || 0) + 1;
    htmx.ajax("GET", `${this.listUrl}?${this.listQuery().toString()}`, {
      target: "#artwork-list-body",
      swap: "innerHTML",
    });
  },
  applyListState() {
    const list = document.getElementById("artwork-list");
    if (list) {
      list.classList.toggle("is-grid", this.viewMode === "grid");
      list.classList.toggle("is-sortable", this.canDrag());
      list.classList.toggle("is-delete-mode", this.deleteMode);
    }
    this.syncSelectedDom();
    this.syncSortable();
  },
};

document.body.addEventListener("htmx:beforeRequest", (event) => {
  if (event.detail.target?.id !== "artwork-list-body") return;
  const store = getAlpine()?.store("vorArtworks");
  if (!store) return;
  event.detail.xhr.__vorSeq = store._reloadSeq;
});

document.body.addEventListener("htmx:beforeSwap", (event) => {
  if (event.detail.target?.id !== "artwork-list-body") return;
  const store = getAlpine()?.store("vorArtworks");
  if (!store) return;
  const requestSeq = event.detail.xhr.__vorSeq;
  if (requestSeq != null && Number(requestSeq) !== store._reloadSeq) {
    event.detail.shouldSwap = false;
    event.detail.isError = false;
  }
});
