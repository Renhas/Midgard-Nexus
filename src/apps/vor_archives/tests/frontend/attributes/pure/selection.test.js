import { describe, expect, it } from "vitest";
import { buildDeletePreviewUrl, hasSelectedId, toggleSelectedId } from "@vor/attributes/pure/selection";

describe("toggleSelectedId", () => {
  it("adds id when not present", () => {
    expect(toggleSelectedId(["1", "2"], 3)).toEqual(["1", "2", "3"]);
  });

  it("removes id when already present", () => {
    expect(toggleSelectedId(["1", "2", "3"], "2")).toEqual(["1", "3"]);
  });

  it("does not mutate original array", () => {
    const source = ["1"];
    const result = toggleSelectedId(source, "2");
    expect(source).toEqual(["1"]);
    expect(result).toEqual(["1", "2"]);
  });

  it("ignores empty id", () => {
    expect(toggleSelectedId(["1"], "")).toEqual(["1"]);
  });
});

describe("hasSelectedId", () => {
  it("checks membership with string coercion", () => {
    expect(hasSelectedId(["1", "book:5"], 1)).toBe(true);
    expect(hasSelectedId(["1", "book:5"], "book:5")).toBe(true);
    expect(hasSelectedId(["1", "book:5"], 2)).toBe(false);
  });
});

describe("buildDeletePreviewUrl", () => {
  it("builds encoded query string for simple and composite ids", () => {
    expect(buildDeletePreviewUrl("/vor/attributes/genres/delete/preview/", ["book:1", "film:2"])).toBe(
      "/vor/attributes/genres/delete/preview/?ids=book%3A1&ids=film%3A2",
    );
  });

  it("returns empty string when baseUrl or ids missing", () => {
    expect(buildDeletePreviewUrl("", ["1"])).toBe("");
    expect(buildDeletePreviewUrl("/preview/", [])).toBe("");
  });
});
