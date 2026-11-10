import { describe, expect, it } from "vitest";
import { readCookie } from "@vor/shared/pure/cookies";

describe("readCookie", () => {
  it("returns empty string when cookie missing", () => {
    expect(readCookie("", "csrftoken")).toBe("");
    expect(readCookie("sessionid=abc", "csrftoken")).toBe("");
  });
  it("returns single cookie value", () => {
    expect(readCookie("csrftoken=abc123", "csrftoken")).toBe("abc123");
  });
  it("returns value from middle of cookie string", () => {
    expect(readCookie("a=1; csrftoken=xyz; b=2", "csrftoken")).toBe("xyz");
  });
  it("returns empty string for empty input", () => {
    expect(readCookie("", "")).toBe("");
    expect(readCookie(undefined, "x")).toBe("");
  });
  it("does not throw on trailing separators", () => {
    expect(readCookie("csrftoken=abc;", "csrftoken")).toBe("abc");
  });
  it("does not match substring of another cookie name", () => {
    expect(readCookie("xcsrftoken=evil; csrftoken=good", "csrftoken")).toBe("good");
  });
});
