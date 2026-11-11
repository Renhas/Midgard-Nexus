import { describe, expect, it } from "vitest";
import {
  filterCatalogue,
  isSelected,
  toggleSelection,
  addSelection,
  removeSelection,
} from "@vor/artworks/pure/catalogs";

describe("filterCatalogue", () => {
  const items = [
    { id: 1, name: "Alpha" },
    { id: 2, name: "Beta" },
    { id: 3, name: "gamma" },
  ];
  it("returns all for empty query", () => {
    expect(filterCatalogue(items, "")).toEqual(items);
    expect(filterCatalogue(items, undefined)).toEqual(items);
  });
  it("filters case-insensitive", () => {
    expect(filterCatalogue(items, "alpha")).toEqual([items[0]]);
    expect(filterCatalogue(items, "GAMMA")).toEqual([items[2]]);
  });
  it("returns empty array for no match", () => {
    expect(filterCatalogue(items, "zzz")).toEqual([]);
  });
  it("handles null items", () => {
    expect(filterCatalogue(null, "x")).toEqual([]);
  });
  it("handles items without name", () => {
    expect(filterCatalogue([{ id: 1 }], "x")).toEqual([]);
  });
});

describe("isSelected", () => {
  const list = [{ id: 1 }, { id: 2 }];
  it("true when id present", () => {
    expect(isSelected(list, 1)).toBe(true);
    expect(isSelected(list, "2")).toBe(true);
  });
  it("false when id absent", () => {
    expect(isSelected(list, 3)).toBe(false);
  });
  it("false for null list", () => {
    expect(isSelected(null, 1)).toBe(false);
  });
});

describe("toggleSelection", () => {
  const a = { id: 1 };
  const b = { id: 2 };
  it("adds when missing", () => {
    expect(toggleSelection([a], b)).toEqual([a, b]);
  });
  it("removes when present", () => {
    expect(toggleSelection([a, b], a)).toEqual([b]);
  });
  it("handles empty list", () => {
    expect(toggleSelection([], a)).toEqual([a]);
  });
  it("matches by numeric id", () => {
    expect(toggleSelection([{ id: 1 }], { id: "1" })).toEqual([]);
  });
});

describe("addSelection", () => {
  const a = { id: 1 };
  it("adds new item", () => {
    expect(addSelection([], a)).toEqual([a]);
  });
  it("does not add duplicate", () => {
    expect(addSelection([a], a)).toEqual([a]);
  });
  it("handles null list", () => {
    expect(addSelection(null, a)).toEqual([a]);
  });
});

describe("removeSelection", () => {
  it("removes by id", () => {
    expect(removeSelection([{ id: 1 }, { id: 2 }], 1)).toEqual([{ id: 2 }]);
  });
  it("handles missing id", () => {
    const list = [{ id: 1 }];
    expect(removeSelection(list, 99)).toEqual(list);
  });
  it("handles null list", () => {
    expect(removeSelection(null, 1)).toEqual([]);
  });
  it("matches by numeric id", () => {
    expect(removeSelection([{ id: 1 }], "1")).toEqual([]);
  });
});
