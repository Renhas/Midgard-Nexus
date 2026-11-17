import { describe, expect, it } from "vitest";
import {
  progressValueLabel,
  progressSuffix,
  progressCh,
  clampProgress,
  parseProgressDraft,
} from "@vor/artworks/pure/progress";

describe("progressValueLabel", () => {
  it("returns integer as string", () => {
    expect(progressValueLabel(5)).toBe("5");
  });
  it("rounds to one decimal", () => {
    expect(progressValueLabel(5.25)).toBe("5.3");
    expect(progressValueLabel(5.14)).toBe("5.1");
  });
  it("handles null/undefined as 0", () => {
    expect(progressValueLabel(null)).toBe("0");
    expect(progressValueLabel(undefined)).toBe("0");
  });
});

describe("progressSuffix", () => {
  it("includes max and unit when max provided", () => {
    expect(progressSuffix(100, "стр")).toBe("/100 стр");
  });
  it("returns unit when max is null", () => {
    expect(progressSuffix(null, "стр")).toBe("стр");
  });
  it("trims trailing space when unit missing", () => {
    expect(progressSuffix(100, "")).toBe("/100");
  });
  it("returns empty when both empty", () => {
    expect(progressSuffix(null, "")).toBe("");
    expect(progressSuffix(undefined, undefined)).toBe("");
  });
});

describe("progressCh", () => {
  it("returns digit count of max", () => {
    expect(progressCh(100)).toBe(3);
    expect(progressCh(9)).toBe(1);
  });
  it("falls back to 4 when max is null", () => {
    expect(progressCh(null)).toBe(4);
    expect(progressCh(undefined)).toBe(4);
  });
});

describe("clampProgress", () => {
  it("clamps to zero", () => {
    expect(clampProgress(-5, 100)).toBe(0);
    expect(clampProgress(-5, null)).toBe(0);
  });
  it("clamps to max", () => {
    expect(clampProgress(150, 100)).toBe(100);
  });
  it("rounds to one decimal", () => {
    expect(clampProgress(3.14, null)).toBe(3.1);
    expect(clampProgress(3.16, null)).toBe(3.2);
  });
});

describe("parseProgressDraft", () => {
  it("parses integer string", () => {
    expect(parseProgressDraft("5")).toBe(5);
  });
  it("parses decimal with comma", () => {
    expect(parseProgressDraft("5,5")).toBe(5.5);
  });
  it("parses decimal with dot", () => {
    expect(parseProgressDraft("5.5")).toBe(5.5);
  });
  it("returns 0 for empty string (matches Number(''))", () => {
    expect(parseProgressDraft("")).toBe(0);
  });
  it("returns null for non-numeric", () => {
    expect(parseProgressDraft("abc")).toBeNull();
  });
  it("returns null for undefined draft", () => {
    expect(parseProgressDraft(undefined)).toBeNull();
  });
});
