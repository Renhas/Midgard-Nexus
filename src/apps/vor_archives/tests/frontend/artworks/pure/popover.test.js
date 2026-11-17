import { describe, expect, it } from "vitest";
import { computeTipLayout, computePopupLayout } from "@vor/artworks/pure/popover";

function rect({ left = 0, top = 0, width = 50, height = 20 } = {}) {
  return {
    left,
    top,
    right: left + width,
    bottom: top + height,
    width,
    height,
  };
}

describe("computeTipLayout", () => {
  it("places tip to the right, centered vertically", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 100, top: 100 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.left).toBe(156);
    expect(layout.top).toBe(110);
    expect(layout.shiftY).toBe(0);
  });
  it("flips to the left when it overflows the right edge", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 850, top: 100 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.left).toBe(644);
    expect(layout.shiftY).toBe(0);
  });
  it("never places left below pad on flip", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 10, top: 100 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 200,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.left).toBe(8);
  });
  it("shifts up when overflowing the bottom edge", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 100, top: 780 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.left).toBe(156);
    expect(layout.top).toBe(790);
    expect(layout.shiftY).toBe(-48);
  });
  it("shifts down when overflowing the top edge", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 100, top: 10 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.shiftY).toBe(38);
  });
  it("uses default pad when not passed", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 100, top: 100 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
    });
    expect(layout.left).toBe(156);
    expect(layout.shiftY).toBe(0);
  });
  it("flips horizontally and shifts vertically in the top-right corner", () => {
    const layout = computeTipLayout({
      chipRect: rect({ left: 850, top: 780 }),
      tipSize: { width: 200, height: 100 },
      viewportWidth: 1000,
      viewportHeight: 800,
      pad: 8,
    });
    expect(layout.left).toBe(644);
    expect(layout.top).toBe(790);
    expect(layout.shiftY).toBe(-48);
  });
});

describe("computePopupLayout", () => {
  it("does not flip when popup fits", () => {
    expect(
      computePopupLayout({
        popupRect: { right: 500, bottom: 500 },
        viewportWidth: 1000,
        viewportHeight: 800,
        pad: 8,
      }),
    ).toEqual({ flipH: false, flipV: false });
  });
  it("flips horizontally when overflowing right edge", () => {
    expect(
      computePopupLayout({
        popupRect: { right: 995, bottom: 500 },
        viewportWidth: 1000,
        viewportHeight: 800,
        pad: 8,
      }),
    ).toEqual({ flipH: true, flipV: false });
  });
  it("flips vertically when overflowing bottom edge", () => {
    expect(
      computePopupLayout({
        popupRect: { right: 500, bottom: 795 },
        viewportWidth: 1000,
        viewportHeight: 800,
        pad: 8,
      }),
    ).toEqual({ flipH: false, flipV: true });
  });
  it("can flip both", () => {
    expect(
      computePopupLayout({
        popupRect: { right: 999, bottom: 799 },
        viewportWidth: 1000,
        viewportHeight: 800,
        pad: 8,
      }),
    ).toEqual({ flipH: true, flipV: true });
  });
  it("uses default pad when not passed", () => {
    expect(
      computePopupLayout({
        popupRect: { right: 993, bottom: 500 },
        viewportWidth: 1000,
        viewportHeight: 800,
      }),
    ).toEqual({ flipH: true, flipV: false });
  });
});
