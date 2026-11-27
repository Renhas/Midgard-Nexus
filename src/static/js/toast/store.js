import { getAlpine } from "@lib/alpine";
import { computeStackSlots, createToastEntry, readToastConfig } from "@toast/stack";

const EXIT_ANIMATION_MS = 220;
const COLLAPSE_DELAY_MS = 180;

export function createToastStore(initialConfig = null) {
  let seq = 0;
  let collapseTimer = null;

  function cancelCollapse() {
    if (collapseTimer !== null) {
      window.clearTimeout(collapseTimer);
      collapseTimer = null;
    }
  }

  return {
    items: [],
    expanded: false,
    config: initialConfig,

    init() {
      if (!this.config) {
        this.config = readToastConfig();
      }
    },

    get visibleItems() {
      return computeStackSlots(this.items);
    },

    get hasMultiple() {
      return this.items.length > 1;
    },

    expand() {
      cancelCollapse();
      if (this.items.length > 0) {
        this.expanded = true;
      }
    },

    scheduleCollapse() {
      cancelCollapse();
      collapseTimer = window.setTimeout(() => {
        collapseTimer = null;
        this.expanded = false;
      }, COLLAPSE_DELAY_MS);
    },

    onFocusIn(event) {
      if (event?.target?.matches?.(":focus-visible")) {
        this.expand();
      }
    },

    onFocusOut() {
      this.scheduleCollapse();
    },

    show(payload) {
      if (!this.config) {
        this.init();
      }
      const id = ++seq;
      const entry = createToastEntry(payload, id, this.config);
      if (!entry.message) {
        return null;
      }
      this.items.push(entry);
      const active = this.items.filter((item) => !item.closing);
      if (active.length > this.config.maxVisible) {
        const oldest = active[0];
        if (oldest) {
          this.dismiss(oldest.id);
        }
      }
      return id;
    },

    onProgressEnd(id) {
      this.dismiss(id);
    },

    dismiss(id) {
      const target = this.items.find((item) => item.id === id);
      if (!target || target.closing) {
        return;
      }
      target.closing = true;
      window.setTimeout(() => {
        this.items = this.items.filter((item) => item.id !== id);
        if (this.items.length === 0) {
          cancelCollapse();
          this.expanded = false;
        }
      }, EXIT_ANIMATION_MS);
    },

    dismissAll() {
      cancelCollapse();
      this.items.forEach((item) => {
        item.closing = true;
      });
      window.setTimeout(() => {
        this.items = [];
        this.expanded = false;
      }, EXIT_ANIMATION_MS);
    },

    triggerAction(item) {
      if (!item?.action) {
        return;
      }
      if (typeof item.action.onClick === "function") {
        item.action.onClick();
      } else if (item.action.event) {
        document.body.dispatchEvent(
          new CustomEvent(item.action.event, {
            detail: item.action.detail,
            bubbles: true,
          }),
        );
      }
      this.dismiss(item.id);
    },

    async copyDetails(item, event) {
      event?.currentTarget?.blur?.();
      if (!item?.details || !navigator.clipboard?.writeText) {
        return;
      }
      try {
        await navigator.clipboard.writeText(item.details);
        item.copied = true;
        window.setTimeout(() => {
          item.copied = false;
        }, 1500);
      } catch {
        // clipboard unavailable
      }
    },
  };
}

document.addEventListener("alpine:init", () => {
  getAlpine()?.store("toasts", createToastStore());
});
