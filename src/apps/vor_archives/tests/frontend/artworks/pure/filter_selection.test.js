import { describe, expect, it } from "vitest";
import { mergeFilterSelection } from "@vor/artworks/pure/filter_selection";

describe("mergeFilterSelection", () => {
  const catalog = [1, 2, 3, 4];

  it("returns all catalog entries when nothing saved", () => {
    expect(mergeFilterSelection(catalog, null, null)).toEqual([1, 2, 3, 4]);
  });
  it("returns empty for empty catalog", () => {
    expect(mergeFilterSelection([], null, null)).toEqual([]);
  });
  it("returns all when all saved as selected", () => {
    expect(mergeFilterSelection(catalog, [1, 2, 3, 4], [1, 2, 3, 4]))
      .toEqual([1, 2, 3, 4]);
  });
  it("excludes known-but-unselected", () => {
    expect(mergeFilterSelection(catalog, [1, 2], [1, 2, 3, 4]))
      .toEqual([1, 2]);
  });
  it("includes unknown (new) entries", () => {
    expect(mergeFilterSelection([1, 2, 3, 4, 5], [1, 2], [1, 2, 3, 4]))
      .toEqual([1, 2, 5]);
  });
  it("compares by string key", () => {
    expect(mergeFilterSelection(["a", "b"], ["a"], ["a", "b"])).toEqual(["a"]);
  });
  it("handles undefined selected", () => {
    expect(mergeFilterSelection([1, 2], undefined, [1])).toEqual([2]);
  });
});
