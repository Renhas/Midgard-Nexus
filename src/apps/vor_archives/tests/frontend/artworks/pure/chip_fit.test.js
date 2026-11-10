import { describe, expect, it } from "vitest";
import {
  allChipsFit,
  computeVisibleChipCount,
} from "@vor/artworks/pure/chip_fit";

describe("allChipsFit", () => {
  it("true when sum fits", () => {
    expect(allChipsFit([100, 100, 100], 400, 10)).toBe(true);
  });
  it("true when sum exactly matches", () => {
    expect(allChipsFit([100, 100, 100], 320, 10)).toBe(true);
  });
  it("false when sum exceeds", () => {
    expect(allChipsFit([100, 100, 100], 300, 10)).toBe(false);
  });
  it("true for empty list with positive available", () => {
    expect(allChipsFit([], 100, 10)).toBe(true);
  });
  it("false when available <= 0", () => {
    expect(allChipsFit([100], 0, 10)).toBe(false);
    expect(allChipsFit([100], -5, 10)).toBe(false);
  });
  it("handles null chipWidths", () => {
    expect(allChipsFit(null, 100, 10)).toBe(true);
  });
  it("zero gap", () => {
    expect(allChipsFit([100, 100], 200, 0)).toBe(true);
    expect(allChipsFit([100, 100], 199, 0)).toBe(false);
  });
});

describe("computeVisibleChipCount", () => {
  it("returns 0/all when available <= 0", () => {
    expect(computeVisibleChipCount({
      chipWidths: [10, 10], available: 0, gap: 5, moreWidth: 40,
    })).toEqual({ visibleCount: 0, hiddenCount: 2 });
  });
  it("hides some to make room for more", () => {
    // Each chip 100, gap 10, more 40, available 350.
    // i=0: next=100, 100+10+40=150 <= 350 -> visible 1, used 100
    // i=1: next=210, 210+10+40=260 <= 350 -> visible 2, used 210
    // i=2: next=320, 320+10+40=370 > 350 -> break
    expect(computeVisibleChipCount({
      chipWidths: [100, 100, 100], available: 350, gap: 10, moreWidth: 40,
    })).toEqual({ visibleCount: 2, hiddenCount: 1 });
  });
  it("hides all when only more fits", () => {
    // available 60, more 40, chip 100 -> cannot fit even one
    expect(computeVisibleChipCount({
      chipWidths: [100, 100], available: 60, gap: 10, moreWidth: 40,
    })).toEqual({ visibleCount: 0, hiddenCount: 2 });
  });
  it("shows all when everything fits including more budget", () => {
    expect(computeVisibleChipCount({
      chipWidths: [10, 10], available: 500, gap: 5, moreWidth: 40,
    })).toEqual({ visibleCount: 2, hiddenCount: 0 });
  });
  it("handles empty chipWidths", () => {
    expect(computeVisibleChipCount({
      chipWidths: [], available: 100, gap: 5, moreWidth: 40,
    })).toEqual({ visibleCount: 0, hiddenCount: 0 });
  });
  it("zero gap", () => {
    // chip 100, more 40, available 250:
    // i=0: next=100, 100+0+40=140<=250 -> v=1, used=100
    // i=1: next=200, 200+0+40=240<=250 -> v=2, used=200
    // i=2: next=300, 300+0+40=340>250 -> break
    expect(computeVisibleChipCount({
      chipWidths: [100, 100, 100], available: 250, gap: 0, moreWidth: 40,
    })).toEqual({ visibleCount: 2, hiddenCount: 1 });
  });
});
