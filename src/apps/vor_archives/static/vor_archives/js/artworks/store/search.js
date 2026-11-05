import { htmx } from "@lib/htmx";
import { VorApi } from "@vor/artworks/api";
import { syncPageScrollLock } from "@vor/common";

export const searchMixin =  {
  searchUrl: "",
  attachUrl: "",
  searchOpen: false,
  searchQuery: "",
  searchTimer: null,

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
  async attachFromSearch(typeKey, workId) {
    const data = await VorApi.attachWorkFromSearch(
      this.attachUrl, typeKey, workId,
    );
    if (!data?.ok) {
      return;
    }
    this.reloadList();
    this.runSearch();
  },
  openWork(url) {
    this.closeSearch();
    htmx.ajax("GET", url, {
      target: "#vor-overlay",
      swap: "innerHTML",
    });
  },
};
