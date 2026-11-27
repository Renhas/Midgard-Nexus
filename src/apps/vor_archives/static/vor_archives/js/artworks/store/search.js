import { htmx } from "@lib/htmx";
import { vorNotify } from "@vor/shared/toasts";
import { VorApi } from "@vor/artworks/api";
import { syncPageScrollLock } from "@vor/shared/scroll_lock";

export const searchMixin = {
  searchUrl: "",
  attachUrl: "",
  searchOpen: false,
  searchQuery: "",
  searchTimer: null,
  _attaching: false,

  openSearch() {
    if (this.searchOpen) {
      document.getElementById("vor-library-search-input")?.focus();
      return;
    }
    this.searchOpen = true;
    syncPageScrollLock();
    this.searchQuery = "";
    const results = document.getElementById("vor-library-search-results");
    if (results) {
      results.innerHTML = "";
    }
    queueMicrotask(() => document.getElementById("vor-library-search-input")?.focus());
  },
  closeSearch() {
    this.searchOpen = false;
    syncPageScrollLock();
    this.searchQuery = "";
    const results = document.getElementById("vor-library-search-results");
    if (results) {
      results.innerHTML = "";
    }
  },
  onSearchInput() {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.runSearch(), 280);
  },
  runSearch() {
    const query = String(this.searchQuery || "").trim();
    const results = document.getElementById("vor-library-search-results");
    if (!query || !this.searchUrl) {
      if (results) {
        results.innerHTML = "";
      }
      return;
    }
    htmx.ajax("GET", `${this.searchUrl}?q=${encodeURIComponent(query)}`, {
      target: "#vor-library-search-results",
      swap: "innerHTML",
    });
  },
  async attachFromSearch(typeKey, workId, title = "", workUrl = "") {
    if (this._attaching) {
      return;
    }
    this._attaching = true;
    try {
      const data = await VorApi.attachWorkFromSearch(this.attachUrl, typeKey, workId);
      if (!data?.ok) {
        return;
      }
      vorNotify.workAttached({ title, url: workUrl }, (url) => this.openWork(url));
      this.reloadList();
      this.runSearch();
    } finally {
      this._attaching = false;
    }
  },
  openWork(url) {
    this.closeSearch();
    htmx.ajax("GET", url, {
      target: "#vor-overlay",
      swap: "innerHTML",
    });
  },
};
