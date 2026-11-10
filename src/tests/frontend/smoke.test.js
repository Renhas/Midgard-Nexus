import { describe, expect, it } from "vitest";

describe("vendor libraries", () => {
  it.each([
    ["alpine", "../../static/js/lib/alpine.js"],
    ["htmx", "../../static/js/lib/htmx.js"],
    ["chart", "../../static/js/lib/chart.js"],
    ["sortable", "../../static/js/lib/sortable.js"],
  ])("imports %s without throwing", async (_name, path) => {
    const mod = await import(path);
    expect(mod).toBeDefined();
  });
});

describe("vor_archives artworks page", () => {
  it("entry point imports without throwing", async () => {
    const mod = await import(
      "../../apps/vor_archives/static/vor_archives/js/pages/artworks.js"
    );
    expect(mod).toBeDefined();
  });
});
