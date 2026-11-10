import { describe, expect, it } from "vitest";
import { wheelDirection } from "@vor/shared/pure/wheel";

describe("wheelDirection", () => {
  it("returns 1 for negative deltaY", () => {
    expect(wheelDirection(-100)).toBe(1);
  });
  it("returns -1 for positive deltaY", () => {
    expect(wheelDirection(100)).toBe(-1);
  });
  it("returns 0 for zero deltaY", () => {
    expect(wheelDirection(0)).toBe(0);
  });
  it("treats undefined/null as zero", () => {
    expect(wheelDirection(undefined)).toBe(0);
    expect(wheelDirection(null)).toBe(0);
  });
});
