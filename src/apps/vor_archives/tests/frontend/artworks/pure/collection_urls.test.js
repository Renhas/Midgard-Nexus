import { describe, expect, it } from "vitest";
import { getCollectionUrl } from "@vor/artworks/pure/collection_urls";

describe("getCollectionUrl", () => {
  it("builds url with trailing slash", () => {
    expect(getCollectionUrl("/col/", 5)).toBe("/col/5/");
  });
  it("appends rest", () => {
    expect(getCollectionUrl("/col/", 5, "items/")).toBe("/col/5/items/");
  });
  it("accepts string ids", () => {
    expect(getCollectionUrl("/col/", "abc", "edit/")).toBe("/col/abc/edit/");
  });
});
