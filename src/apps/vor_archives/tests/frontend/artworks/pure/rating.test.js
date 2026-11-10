import { describe, expect, it } from "vitest";
import { displayRating, ratingLabel, starState } from "@vor/artworks/pure/rating";

describe("displayRating", () => {
  it("prefers hover over rating", () => {
    expect(displayRating(3, 5)).toBe(5);
  });
  it("falls back to rating", () => {
    expect(displayRating(3, 0)).toBe(3);
    expect(displayRating(3, undefined)).toBe(3);
  });
  it("returns 0 when both empty", () => {
    expect(displayRating(0, 0)).toBe(0);
    expect(displayRating(null, null)).toBe(0);
    expect(displayRating(undefined, undefined)).toBe(0);
  });
});

describe("ratingLabel", () => {
  it("returns dash for 0", () => {
    expect(ratingLabel(0)).toBe("—");
  });
  it("returns dash for null/undefined", () => {
    expect(ratingLabel(null)).toBe("—");
    expect(ratingLabel(undefined)).toBe("—");
  });
  it("returns string for nonzero", () => {
    expect(ratingLabel(3)).toBe("3");
    expect(ratingLabel(4.5)).toBe("4.5");
  });
});

describe("starState", () => {
  it("is-full when value >= star*2", () => {
    expect(starState(10, 5)).toBe("is-full");
    expect(starState(8, 4)).toBe("is-full");
  });
  it("is-half when value === star*2 - 1", () => {
    expect(starState(9, 5)).toBe("is-half");
    expect(starState(7, 4)).toBe("is-half");
  });
  it("is-empty otherwise", () => {
    expect(starState(0, 1)).toBe("is-empty");
    expect(starState(2, 5)).toBe("is-empty");
  });
});
