import { describe, expect, it } from "vitest";
import {
  buildBarRatingItems,
  buildCloudItems,
  buildHistItems,
  buildPieChoiceItems,
  buildPieTypeItems,
  buildSpentItems,
  calcAttrShare,
  calcAttrTotals,
  calcAverageRating,
  formatAverage,
  formatDashPercent,
  formatMetricNumber,
  sumByCol,
  sumByRow,
  sumByRowWithCount,
} from "@vor/dashboard/pure/metrics";

describe("dashboard pure metrics", () => {
  const statusMatrix = {
    book: { planning: 2, completed: 3 },
    film: { planning: 1, completed: 4 },
    game: {},
  };

  const ratingMatrix = {
    book: { "": 1, 8: 2, 10: 1 },
    film: { "": 2, 6: 2 },
    game: {},
  };

  const typeMeta = {
    book: { label: "Книги", unit: "стр.", icon: "bi-book" },
    film: { label: "Фильмы", unit: "сер.", icon: "bi-film" },
    game: { label: "Игры", unit: "ч.", icon: "bi-controller" },
  };

  it("sums matrix rows and columns safely", () => {
    expect(sumByRow("book", statusMatrix)).toBe(5);
    expect(sumByRow("unknown", statusMatrix)).toBe(0);
    expect(sumByCol(["book", "film"], "completed", statusMatrix)).toBe(7);
    expect(sumByCol([], "completed", statusMatrix)).toBe(0);
  });

  it("computes rating totals ignoring unrated items", () => {
    expect(sumByRowWithCount("book", ratingMatrix)).toEqual({ sum: 26, count: 3 });
    expect(sumByRowWithCount("game", ratingMatrix)).toEqual({ sum: 0, count: 0 });
    expect(formatAverage(26, 3)).toBe("8.7");
    expect(formatAverage(0, 0)).toBe("0.0");
    expect(calcAverageRating(["book", "film"], ratingMatrix)).toBe("7.6");
    expect(calcAverageRating([], ratingMatrix)).toBe("0.0");
  });

  it("builds chart datasets for stats tab", () => {
    expect(buildPieTypeItems(typeMeta, statusMatrix)).toEqual([
      { label: "Книги", count: 5 },
      { label: "Фильмы", count: 5 },
      { label: "Игры", count: 0 },
    ]);

    const choices = { planning: { label: "В планах" }, completed: { label: "Завершено" } };
    expect(buildPieChoiceItems(["book"], choices, statusMatrix)).toEqual([
      { label: "В планах", count: 2 },
      { label: "Завершено", count: 3 },
    ]);
    expect(buildPieChoiceItems([], choices, statusMatrix)).toEqual([]);

    expect(buildBarRatingItems(typeMeta, ratingMatrix)).toEqual([
      { label: "Книги", count: "8.7" },
      { label: "Фильмы", count: "6.0" },
      { label: "Игры", count: "0.0" },
    ]);

    expect(buildSpentItems({ book: 120, film: 0 }, typeMeta)).toEqual([
      { key: "book", count: 120, unit: "стр.", icon: "bi-book" },
      { key: "film", count: 0, unit: "сер.", icon: "bi-film" },
    ]);
  });

  it("formats numbers and percentages", () => {
    expect(formatMetricNumber(12.34)).toBe("12.3");
    expect(formatDashPercent(25)).toBe("25%");
    expect(formatDashPercent(0)).toBe("0%");
    expect(calcAttrShare(1, 3)).toBe(33.3);
    expect(calcAttrShare(1, 0)).toBe(0);
  });

  it("prepares attribute totals, histogram and cloud items", () => {
    const attrs = {
      tags: [
        { name: "sci-fi", count: 10 },
        { name: "drama", count: 2 },
        { name: "noir", count: 6 },
      ],
    };

    expect(calcAttrTotals(attrs)).toEqual({ tags: 18 });
    expect(buildHistItems(attrs.tags, 2)).toEqual([
      { label: "sci-fi", count: 10 },
      { label: "drama", count: 2 },
    ]);

    expect(buildCloudItems(attrs.tags, 10, 50)).toEqual([
      { label: "sci-fi", count: 10, size: 50 },
      { label: "drama", count: 2, size: 10 },
      { label: "noir", count: 6, size: 30 },
    ]);

    expect(buildCloudItems([{ name: "solo", count: 5 }], 10, 50)).toEqual([{ label: "solo", count: 5, size: 30 }]);
    expect(buildCloudItems([])).toEqual([]);
  });
});
