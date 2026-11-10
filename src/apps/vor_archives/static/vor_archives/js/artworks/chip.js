import { getAlpine } from "@lib/alpine";
import { allChipsFit, computeVisibleChipCount } from "@vor/artworks/pure/chip_fit";

function tempReveal(el, readWidth) {
  const prevDisplay = el.style.display;
  el.style.display = "inline-flex";
  el.style.visibility = "hidden";
  el.style.position = "absolute";
  const width = readWidth();
  el.style.display = prevDisplay;
  el.style.visibility = "";
  el.style.position = "";
  return width;
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
      this.popupOpen = !this.popupOpen;
      if (this.popupOpen) {
        this.$nextTick(() => this.placePopup());
      }
    },
    fit() {
      const root = this.$el;
      const chips = [...root.querySelectorAll("[data-chip]")];
      const more = this.$refs.more;
      chips.forEach((chip) => {
        chip.style.display = "";
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
        chip.style.display = index < result.visibleCount ? "" : "none";
      });
      this.visibleCount = result.visibleCount;
      this.hiddenCount = result.hiddenCount;
    },
    measureMoreWidth(moreWrap, more) {
      let moreWidth = 48;
      if (moreWrap) {
        return tempReveal(
          moreWrap,
          () => (more && more.offsetWidth) || moreWrap.offsetWidth,
        ) || moreWidth;
      }
      if (more) {
        return tempReveal(more, () => more.offsetWidth) || moreWidth;
      }
      return moreWidth;
    },
    placeTip(chip) {
      const tip = chip.querySelector(".vor-chip-tip");
      if (!tip) {
        return;
      }
      const pad = 8;
      const chipRect = chip.getBoundingClientRect();
      tip.style.position = "fixed";
      tip.style.left = `${chipRect.right + 6}px`;
      tip.style.top = `${chipRect.top + chipRect.height / 2}px`;
      tip.style.right = "auto";
      tip.style.bottom = "auto";
      tip.style.transform = "translateY(-50%)";
      this.$nextTick(() => {
        let rect = tip.getBoundingClientRect();
        if (rect.right > window.innerWidth - pad) {
          tip.style.left = `${Math.max(pad, chipRect.left - rect.width - 6)}px`;
          rect = tip.getBoundingClientRect();
        }
        let shiftY = 0;
        if (rect.bottom > window.innerHeight - pad) {
          shiftY = window.innerHeight - pad - rect.bottom;
        }
        if (rect.top + shiftY < pad) {
          shiftY = pad - rect.top;
        }
        tip.style.transform = `translateY(calc(-50% + ${shiftY}px))`;
      });
    },
    placePopup() {
      const popup = this.$refs.popup;
      if (!popup) {
        return;
      }
      popup.style.top = "calc(100% + 4px)";
      popup.style.left = "0";
      popup.style.right = "auto";
      popup.style.bottom = "auto";
      const pad = 8;
      const rect = popup.getBoundingClientRect();
      if (rect.right > window.innerWidth - pad) {
        popup.style.left = "auto";
        popup.style.right = "0";
      }
      if (rect.bottom > window.innerHeight - pad) {
        popup.style.top = "auto";
        popup.style.bottom = "calc(100% + 4px)";
      }
    },
  }));
});
