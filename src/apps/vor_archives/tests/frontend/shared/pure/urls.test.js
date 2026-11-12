import { describe, expect, it } from "vitest";
import { parseOverlayUrl, isSamePageLink } from "@vor/shared/pure/urls";

describe("parseOverlayUrl", () => {
  it("extracts path and search from raw url", () => {
    expect(parseOverlayUrl("/foo/bar?x=1", "https://example.com")).toBe("/foo/bar?x=1");
  });
  it("returns raw on empty input", () => {
    expect(parseOverlayUrl("", "https://example.com")).toBe("");
  });
  it("returns raw when invalid", () => {
    const raw = "http://[::1";
    expect(parseOverlayUrl(raw, "https://example.com")).toBe(raw);
  });
  it("resolves relative url against base origin", () => {
    expect(parseOverlayUrl("foo", "https://example.com")).toBe("/foo");
  });
});

describe("isSamePageLink", () => {
  const location = {
    origin: "https://example.com",
    pathname: "/vor/artworks/",
    search: "",
  };
  it("returns true for same page", () => {
    expect(isSamePageLink("/vor/artworks/", "", location)).toBe(true);
  });
  it("returns false for different path", () => {
    expect(isSamePageLink("/vor/other/", "", location)).toBe(false);
  });
  it("returns false for different search", () => {
    expect(isSamePageLink("/vor/artworks/?x=1", "", location)).toBe(false);
  });
  it("returns false for external origin", () => {
    expect(isSamePageLink("https://other.com/vor/artworks/", "", location)).toBe(false);
  });
  it("returns false for _blank target", () => {
    expect(isSamePageLink("/vor/artworks/", "_blank", location)).toBe(false);
  });
  it("returns true for _self target", () => {
    expect(isSamePageLink("/vor/artworks/", "_self", location)).toBe(true);
  });
  it("returns false for empty href", () => {
    expect(isSamePageLink("", "", location)).toBe(false);
  });
  it("returns false for invalid href", () => {
    expect(isSamePageLink("http://[::1", "", location)).toBe(false);
  });
});
