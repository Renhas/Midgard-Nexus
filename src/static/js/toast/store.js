import { getAlpine } from "@lib/alpine";
import { computeStackSlots, createToastEntry, readToastConfig } from "@toast/stack";

const EXIT_ANIMATION_MS = 220;
const MAX_QUEUE_SIZE = 50;
const HOVER_BOUNDARY_PAD = 8;

export function createToastStore(initialConfig = null) {
  let seq = 0;
  let trackHandler = null;
  let pointerActive = false;
  let keyboardFocus = false;

  function stopTrackingPointer() {
    if (trackHandler) {
      document.removeEventListener("pointermove", trackHandler, true);
      trackHandler = null;
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
      const limit = this.config?.maxVisible;
      return computeStackSlots(this.items, limit);
    },

    get hasMultiple() {
      return this.visibleItems.length > 1;
    },

    expand(viewportEl = null) {
      if (this.items.length === 0) {
        return;
      }
      pointerActive = true;
      this.expanded = true;
      if (viewportEl && !trackHandler) {
        trackHandler = (event) => {
          if (!this.expanded) {
            stopTrackingPointer();
            return;
          }
          const rect = viewportEl.getBoundingClientRect();
          const inside =
            event.clientX >= rect.left - HOVER_BOUNDARY_PAD &&
            event.clientX <= rect.right + HOVER_BOUNDARY_PAD &&
            event.clientY >= rect.top - HOVER_BOUNDARY_PAD &&
            event.clientY <= rect.bottom + HOVER_BOUNDARY_PAD;
          if (!inside) {
            this.collapse();
          }
        };
        document.addEventListener("pointermove", trackHandler, true);
      }
    },

    collapse() {
      stopTrackingPointer();
      pointerActive = false;
      keyboardFocus = false;
      this.expanded = false;
    },

    onFocusIn(event) {
      if (event?.target?.matches?.(":focus-visible") && this.items.length > 0) {
        keyboardFocus = true;
        this.expanded = true;
      }
    },

    onFocusOut(event) {
      const nextTarget = event?.relatedTarget;
      if (nextTarget && event.currentTarget?.contains?.(nextTarget)) {
        return;
      }
      keyboardFocus = false;
      if (!pointerActive) {
        this.collapse();
      }
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
      if (this.items.length > MAX_QUEUE_SIZE) {
        this.items.splice(0, this.items.length - MAX_QUEUE_SIZE);
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
          this.collapse();
        }
      }, EXIT_ANIMATION_MS);
    },

    dismissAll() {
      this.items.forEach((item) => {
        item.closing = true;
      });
      window.setTimeout(() => {
        this.items = [];
        this.collapse();
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
