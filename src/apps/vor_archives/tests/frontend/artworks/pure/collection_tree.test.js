import { describe, expect, it } from "vitest";
import { flattenCollectionTree } from "@vor/artworks/pure/collection_tree";

describe("flattenCollectionTree", () => {
  it("returns empty for null", () => {
    expect(flattenCollectionTree(null)).toEqual([]);
  });
  it("returns empty for empty array", () => {
    expect(flattenCollectionTree([])).toEqual([]);
  });
  it("flattens flat tree with level 0", () => {
    expect(
      flattenCollectionTree([
        { id: 1, name: "A" },
        { id: 2, name: "B" },
      ]),
    ).toEqual([
      { id: 1, name: "A", in_collection: false, level: 0 },
      { id: 2, name: "B", in_collection: false, level: 0 },
    ]);
  });
  it("flattens nested tree and tracks level", () => {
    expect(
      flattenCollectionTree([
        { id: 1, name: "A", children: [{ id: 2, name: "B", children: [{ id: 3, name: "C" }] }] },
        { id: 4, name: "D" },
      ]),
    ).toEqual([
      { id: 1, name: "A", in_collection: false, level: 0 },
      { id: 2, name: "B", in_collection: false, level: 1 },
      { id: 3, name: "C", in_collection: false, level: 2 },
      { id: 4, name: "D", in_collection: false, level: 0 },
    ]);
  });
  it("preserves in_collection flag", () => {
    const tree = [{ id: 1, name: "A", in_collection: true }];
    expect(flattenCollectionTree(tree)[0].in_collection).toBe(true);
  });
});
