import { getAlpine } from "@lib/alpine";
import { allChipsFit, computeVisibleChipCount } from "@vor/artworks/pure/chip_fit";
import { computeTipLayout, computePopupLayout } from "@vor/artworks/pure/popover";

function measureHidden(el, display, fn) {
  const prevDisplay = el.style.display;
  const prevVisibility = el.style.visibility;
  el.style.display = display;
  el.style.visibility = "hidden";
  try {
    return fn();
  } finally {
    el.style.display = prevDisplay;
    el.style.visibility = prevVisibility;
  }
}

function tempReveal(el, readWidth) {
  const prevPosition = el.style.position;
  el.style.position = "absolute";
  try {
    return measureHidden(el, "inline-flex", readWidth);
  } finally {
    el.style.position = prevPosition;
  }
}

document.addEventListener("alpine:init", () => {
  getAlpine().data("vorChipOverflow", () => ({
    hiddenCount: 0,
    visibleCount: 0,
    popupOpen: false,
    overlayData() {
      const root = this.$el.closest(".vor-overlay");
      const alpine = getAlpine();
      return root && alpine ? alpine.$data(root) : null;
    },
    canTogglePlatform() {
      return Boolean(this.overlayData()?.canTogglePlatform());
    },
    platformOff(id) {
      return Boolean(this.overlayData()?.platformOff(id));
    },
    togglePlatform(id) {
      this.overlayData()?.togglePlatform(id);
    },
    init() {
      this._ro = new ResizeObserver(() => this.fit());
      this._ro.observe(this.$el);
      this.$nextTick(() => this.fit());
    },
    destroy() {
      this._ro?.disconnect();
    },
    togglePopup() {
      if (this.popupOpen) {
        this.popupOpen = false;
        return;
      }
      const popup = this.$refs.popup;
      if (popup) {
        measureHidden(popup, "block", () => this.placePopup());
      }
      this.popupOpen = true;
    },
    fit() {
      const root = this.$el;
      const chips = [...root.querySelectorAll("[data-chip]")];
      const more = this.$refs.more;
      chips.forEach((chip) => {
        chip.classList.remove("vor-chip--hidden");
      });
      const available = root.clientWidth;
      if (available <= 0) {
        return;
      }
      const gap = parseFloat(getComputedStyle(root).columnGap || getComputedStyle(root).gap) || 6.4;
      const chipWidths = chips.map((chip) => chip.offsetWidth);
      if (allChipsFit(chipWidths, available, gap)) {
        this.visibleCount = chips.length;
        this.hiddenCount = 0;
        return;
      }
      const moreWidth = this.measureMoreWidth(this.$refs.moreWrap, more);
      const result = computeVisibleChipCount({ chipWidths, available, gap, moreWidth });
      chips.forEach((chip, index) => {
        chip.classList.toggle("vor-chip--hidden", index >= result.visibleCount);
      });
      this.visibleCount = result.visibleCount;
      this.hiddenCount = result.hiddenCount;
    },
    measureMoreWidth(moreWrap, more) {
      let moreWidth = 48;
      if (moreWrap) {
        return tempReveal(moreWrap, () => (more && more.offsetWidth) || moreWrap.offsetWidth) || moreWidth;
      }
      if (more) {
        return tempReveal(more, () => more.offsetWidth) || moreWidth;
      }
      return moreWidth;
    },
    placeTip(chip) {
      const tip = chip.querySelector(".vor-chip__tip");
      if (!tip) {
        return;
      }
      const chipRect = chip.getBoundingClientRect();
      measureHidden(tip, "block", () => {
        const tipRect = tip.getBoundingClientRect();
        const layout = computeTipLayout({
          chipRect,
          tipSize: { width: tipRect.width, height: tipRect.height },
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight,
          pad: 8,
        });
        tip.style.setProperty("--tip-left", `${layout.left}px`);
        tip.style.setProperty("--tip-top", `${layout.top}px`);
        tip.style.setProperty("--tip-shift-y", `${layout.shiftY}px`);
      });
    },
    placePopup() {
      const popup = this.$refs.popup;
      if (!popup) {
        return;
      }
      popup.classList.remove("vor-chip-popup--flipped-h", "vor-chip-popup--flipped-v");
      const rect = popup.getBoundingClientRect();
      const layout = computePopupLayout({
        popupRect: rect,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        pad: 8,
      });
      if (layout.flipH) {
        popup.classList.add("vor-chip-popup--flipped-h");
      }
      if (layout.flipV) {
        popup.classList.add("vor-chip-popup--flipped-v");
      }
    },
  }));
});
