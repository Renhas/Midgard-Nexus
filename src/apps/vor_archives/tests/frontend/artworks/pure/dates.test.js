import { describe, expect, it } from "vitest";
import {
  toIsoDate,
  buildDateCells,
  yearGridStart,
  buildYearCells,
} from "@vor/artworks/pure/dates";

describe("toIsoDate", () => {
  it("pads single-digit month and day", () => {
    expect(toIsoDate(new Date(2024, 0, 5))).toBe("2024-01-05");
  });
  it("keeps two-digit month and day", () => {
    expect(toIsoDate(new Date(2024, 11, 31))).toBe("2024-12-31");
  });
  it("handles leap day", () => {
    expect(toIsoDate(new Date(2024, 1, 29))).toBe("2024-02-29");
  });
});

describe("buildDateCells", () => {
  it("returns 42 cells", () => {
    expect(buildDateCells(new Date(2024, 0, 15))).toHaveLength(42);
  });
  it("marks current month days", () => {
    const cells = buildDateCells(new Date(2024, 4, 15));
    expect(cells.filter((c) => c.current)).toHaveLength(31);
  });
  it("includes leading days from previous month", () => {
    // May 2024 starts on Wednesday; week starts on Monday -> 2 leading days.
    const cells = buildDateCells(new Date(2024, 4, 15));
    expect(cells[0].iso).toBe("2024-04-29");
    expect(cells[1].iso).toBe("2024-04-30");
    expect(cells[2].iso).toBe("2024-05-01");
  });
  it("produces unique iso values", () => {
    const cells = buildDateCells(new Date(2024, 1, 10));
    expect(new Set(cells.map((c) => c.iso)).size).toBe(42);
  });
});

describe("yearGridStart", () => {
  it("rounds down to multiple of 12", () => {
    expect(yearGridStart(2024)).toBe(2016);
    expect(yearGridStart(2016)).toBe(2016);
    expect(yearGridStart(2027)).toBe(2016);
    expect(yearGridStart(2028)).toBe(2028);
  });
});

describe("buildYearCells", () => {
  it("returns 12 consecutive years", () => {
    expect(buildYearCells(2016)).toEqual([
      2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027,
    ]);
  });
});
