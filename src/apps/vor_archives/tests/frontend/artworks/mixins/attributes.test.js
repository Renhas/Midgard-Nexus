import { describe, expect, it } from "vitest";
import { getAttributeMixin } from "@vor/artworks/mixins/attributes";

function mount(opts = {}) {
  return {
    workType: "book",
    authors: [],
    genres: [],
    tags: [],
    platforms: [],
    ...getAttributeMixin(opts),
  };
}

describe("getAttributeMixin", () => {
  it("initializes with closed accordions", () => {
    const ctx = mount();
    expect(ctx.openAttrAccordion).toBeNull();
  });

  it("opens a closed accordion", () => {
    const ctx = mount();
    ctx.toggleAttrAccordion("authors");
    expect(ctx.openAttrAccordion).toBe("authors");
  });

  it("closes currently open accordion on second toggle", () => {
    const ctx = mount();
    ctx.toggleAttrAccordion("authors");
    ctx.toggleAttrAccordion("authors");
    expect(ctx.openAttrAccordion).toBeNull();
  });

  it("switches exclusively between accordions", () => {
    const ctx = mount();
    ctx.toggleAttrAccordion("authors");
    expect(ctx.openAttrAccordion).toBe("authors");

    ctx.toggleAttrAccordion("genres");
    expect(ctx.openAttrAccordion).toBe("genres");

    ctx.toggleAttrAccordion("tags");
    expect(ctx.openAttrAccordion).toBe("tags");
  });

  it("filters catalog items by query case-insensitively", () => {
    const ctx = mount({
      catalogs: {
        book: {
          genres: [
            { id: 1, name: "Киберпанк" },
            { id: 2, name: "Фэнтези" },
          ],
        },
      },
    });
    expect(ctx.filterCatalog("genres", "кибер")).toEqual([{ id: 1, name: "Киберпанк" }]);
    expect(ctx.filterCatalog("genres", "")).toHaveLength(2);
  });

  it("toggles attribute selection", () => {
    const ctx = mount();
    const author = { id: 10, name: "Автор" };
    ctx.toggleAttr("authors", author);
    expect(ctx.hasAttr("authors", 10)).toBe(true);
    ctx.toggleAttr("authors", author);
    expect(ctx.hasAttr("authors", 10)).toBe(false);
  });
});
