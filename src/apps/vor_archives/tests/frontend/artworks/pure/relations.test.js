import { describe, expect, it } from "vitest";
import { allowedRelationTypes, relationKey, relationLabelFor } from "@vor/artworks/pure/relations";

describe("allowedRelationTypes", () => {
  const types = [
    { value: "other", label: "Другое" },
    { value: "sequel", label: "Продолжение" },
    { value: "adaptation", label: "Адаптация" },
    { value: "spin_off", label: "Спин-офф" },
  ];

  it("always includes other", () => {
    expect(allowedRelationTypes(types, "game", "book").some((t) => t.value === "other")).toBe(true);
  });
  it("adaptation only for different types", () => {
    const same = allowedRelationTypes(types, "book", "book");
    expect(same.find((t) => t.value === "adaptation")).toBeUndefined();
    const diff = allowedRelationTypes(types, "film", "book");
    expect(diff.find((t) => t.value === "adaptation")).toBeDefined();
  });
  it("sequel and spin_off only for same type", () => {
    const same = allowedRelationTypes(types, "book", "book");
    expect(same.find((t) => t.value === "sequel")).toBeDefined();
    const diff = allowedRelationTypes(types, "film", "book");
    expect(diff.find((t) => t.value === "sequel")).toBeUndefined();
  });
  it("handles empty otherType", () => {
    const result = allowedRelationTypes(types, "", "book");
    expect(result.find((t) => t.value === "other")).toBeDefined();
    expect(result.find((t) => t.value === "adaptation")).toBeUndefined();
    expect(result.find((t) => t.value === "sequel")).toBeUndefined();
  });
  it("handles missing relationTypes list", () => {
    expect(allowedRelationTypes(undefined, "book", "book")).toEqual([]);
  });
});

describe("relationKey", () => {
  it("uses id when present", () => {
    expect(relationKey({ id: 5, type_key: "book", work_id: 10 })).toBe("5-book-10");
  });
  it("uses 'new' when id is null", () => {
    expect(relationKey({ id: null, type_key: "book", work_id: 10 })).toBe("new-book-10");
  });
  it("uses 'new' when id is undefined", () => {
    expect(relationKey({ type_key: "book", work_id: 10 })).toBe("new-book-10");
  });
  it("uses 'new' when id is 0", () => {
    expect(relationKey({ id: 0, type_key: "book", work_id: 10 })).toBe("new-book-10");
  });
});

describe("relationLabelFor", () => {
  const types = [
    { value: "sequel", label: "Продолжение" },
    { value: "spin_off", label: "Спин-офф" },
    { value: "adaptation", label: "Адаптация" },
    { value: "remake", label: "Ремейк" },
    { value: "custom", label: "Своё" },
  ];
  it("sequel out = Продолжение", () => {
    expect(relationLabelFor(types, "sequel", "out")).toBe("Продолжение");
  });
  it("sequel in = Предыстория", () => {
    expect(relationLabelFor(types, "sequel", "in")).toBe("Предыстория");
  });
  it("adaptation out = Адаптация", () => {
    expect(relationLabelFor(types, "adaptation", "out")).toBe("Адаптация");
  });
  it("adaptation in = Первоисточник", () => {
    expect(relationLabelFor(types, "adaptation", "in")).toBe("Первоисточник");
  });
  it("unknown type falls back to catalog label", () => {
    expect(relationLabelFor(types, "custom", "out")).toBe("Своё");
  });
  it("unknown type with empty catalog falls back to 'Связано'", () => {
    expect(relationLabelFor([], "custom", "out")).toBe("Связано");
  });
});
