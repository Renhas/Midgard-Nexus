import { describe, expect, it } from "vitest";
import { allowedRelationTypes, relationKey, relationLabelFor } from "@vor/artworks/pure/relations";

describe("allowedRelationTypes", () => {
  const rules = [
    { value: "rel_any", label: "Any", reverseLabel: "Any", scope: "any" },
    { value: "rel_same", label: "Same", reverseLabel: "SameRev", scope: "same" },
    { value: "rel_diff", label: "Diff", reverseLabel: "DiffRev", scope: "different" },
  ];

  it("includes scope 'any' regardless of work types", () => {
    expect(allowedRelationTypes(rules, "type_a", "type_b").map((t) => t.value)).toContain("rel_any");
    expect(allowedRelationTypes(rules, "type_a", "type_a").map((t) => t.value)).toContain("rel_any");
  });

  it("includes scope 'different' only when work types differ", () => {
    const same = allowedRelationTypes(rules, "type_a", "type_a").map((t) => t.value);
    const diff = allowedRelationTypes(rules, "type_a", "type_b").map((t) => t.value);
    expect(same).not.toContain("rel_diff");
    expect(diff).toContain("rel_diff");
  });

  it("includes scope 'same' only when work types match", () => {
    const same = allowedRelationTypes(rules, "type_a", "type_a").map((t) => t.value);
    const diff = allowedRelationTypes(rules, "type_a", "type_b").map((t) => t.value);
    expect(same).toContain("rel_same");
    expect(diff).not.toContain("rel_same");
  });

  it("excludes 'same' and 'different' when one of work types is empty", () => {
    const result = allowedRelationTypes(rules, "", "type_a").map((t) => t.value);
    expect(result).toEqual(["rel_any"]);
  });

  it("handles missing rules list", () => {
    expect(allowedRelationTypes(undefined, "type_a", "type_a")).toEqual([]);
  });
});

describe("relationKey", () => {
  it("uses id when present", () => {
    expect(relationKey({ id: 5, type_key: "type_a", work_id: 10 })).toBe("5-type_a-10");
  });

  it("uses 'new' when id is missing or falsy", () => {
    expect(relationKey({ id: null, type_key: "type_a", work_id: 10 })).toBe("new-type_a-10");
    expect(relationKey({ type_key: "type_a", work_id: 10 })).toBe("new-type_a-10");
    expect(relationKey({ id: 0, type_key: "type_a", work_id: 10 })).toBe("new-type_a-10");
  });
});

describe("relationLabelFor", () => {
  const rules = [
    { value: "rel_bidirectional", label: "Forward", reverseLabel: "Backward", scope: "same" },
    { value: "rel_symmetric", label: "Symmetric", scope: "any" },
  ];

  it("returns label for outgoing direction", () => {
    expect(relationLabelFor(rules, "rel_bidirectional", "out")).toBe("Forward");
  });

  it("returns reverseLabel for incoming direction", () => {
    expect(relationLabelFor(rules, "rel_bidirectional", "in")).toBe("Backward");
  });

  it("falls back to label when reverseLabel is omitted", () => {
    expect(relationLabelFor(rules, "rel_symmetric", "in")).toBe("Symmetric");
  });

  it("falls back to default label when type is unknown", () => {
    expect(relationLabelFor(rules, "unknown", "out")).toBe("Связано");
    expect(relationLabelFor([], "rel_bidirectional", "out")).toBe("Связано");
  });
});
