import { describe, expect, it } from "vitest";
import { WORK_FIELD_KEYS, getWorkFieldsMixin } from "@vor/artworks/mixins/work_fields";

function mount(source) {
  return { ...getWorkFieldsMixin(source) };
}

describe("getWorkFieldsMixin", () => {
  it("uses base defaults for missing fields", () => {
    const ctx = mount({});
    expect(ctx.workType).toBe("");
    expect(ctx.filmType).toBe("movie");
    expect(ctx.title).toBe("");
    expect(ctx.pages).toBe("");
    expect(ctx.ageRating).toBe("");
    expect(ctx.authors).toEqual([]);
  });
  it("applies source values", () => {
    const ctx = mount({ workType: "book", title: "T", ageRating: "12+" });
    expect(ctx.workType).toBe("book");
    expect(ctx.title).toBe("T");
    expect(ctx.ageRating).toBe("12+");
  });
  it("falls back to default for null source values", () => {
    const ctx = mount({ workType: null, filmType: null, title: null });
    expect(ctx.workType).toBe("");
    expect(ctx.filmType).toBe("movie");
    expect(ctx.title).toBe("");
  });
  it("keeps zero and empty-string source values", () => {
    const ctx = mount({ pages: 0, title: "" });
    expect(ctx.pages).toBe(0);
    expect(ctx.title).toBe("");
  });
  it("gives independent array instances per call", () => {
    const a = mount({});
    const b = mount({});
    a.authors.push({ id: 1 });
    expect(b.authors).toEqual([]);
  });
});

describe("applyWorkFields", () => {
  it("assigns present keys", () => {
    const ctx = mount({ workType: "book" });
    ctx.applyWorkFields({ title: "t", ageRating: "12+" });
    expect(ctx.title).toBe("t");
    expect(ctx.ageRating).toBe("12+");
    expect(ctx.workType).toBe("book");
  });
  it("ignores undefined values", () => {
    const ctx = mount({});
    ctx.title = "keep";
    ctx.applyWorkFields({ title: undefined });
    expect(ctx.title).toBe("keep");
  });
  it("ignores keys not in WORK_FIELD_KEYS", () => {
    const ctx = mount({});
    ctx.applyWorkFields({ coverPreview: "/x.jpg", relations: [1] });
    expect("coverPreview" in ctx).toBe(false);
    expect("relations" in ctx).toBe(false);
  });
});

describe("resetWorkFields", () => {
  it("returns to source-supplied defaults", () => {
    const ctx = mount({ workType: "book", title: "x" });
    ctx.workType = "film";
    ctx.title = "changed";
    ctx.resetWorkFields();
    expect(ctx.workType).toBe("book");
    expect(ctx.title).toBe("x");
  });
  it("returns to base defaults when no source", () => {
    const ctx = mount({});
    ctx.title = "changed";
    ctx.authors = [{ id: 1 }];
    ctx.resetWorkFields();
    expect(ctx.title).toBe("");
    expect(ctx.authors).toEqual([]);
  });
  it("does not corrupt stored defaults when current arrays are mutated", () => {
    const ctx = mount({});
    ctx.authors.push({ id: 1 });
    ctx.resetWorkFields();
    expect(ctx.authors).toEqual([]);
  });
});

describe("workFieldsSnapshot", () => {
  it("captures current values for all work fields", () => {
    const ctx = mount({});
    ctx.title = "T";
    ctx.ageRating = "16+";
    ctx.authors = [{ id: 1 }];
    const snap = ctx.workFieldsSnapshot();
    expect(snap.title).toBe("T");
    expect(snap.ageRating).toBe("16+");
    expect(snap.authors).toEqual([{ id: 1 }]);
  });
  it("only includes work field keys", () => {
    const ctx = mount({});
    const snap = ctx.workFieldsSnapshot();
    Object.keys(snap).forEach((key) => {
      expect(WORK_FIELD_KEYS).toContain(key);
    });
  });
});
