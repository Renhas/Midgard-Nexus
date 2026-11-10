import { describe, expect, it } from "vitest";
import {
  FIELD_TO_STATE,
  fieldValue,
  fieldIsEmpty,
  collectRequiredFields,
  isRequiredField,
} from "@vor/artworks/pure/form_state";

describe("FIELD_TO_STATE", () => {
  it("marks title with trim", () => {
    expect(FIELD_TO_STATE.title).toEqual({ key: "title", trim: true });
  });
  it("marks non-trim fields", () => {
    expect(FIELD_TO_STATE.pages).toEqual({ key: "pages" });
    expect(FIELD_TO_STATE.duration_minutes.key).toBe("durationMinutes");
    expect(FIELD_TO_STATE.episode_count.key).toBe("episodeCount");
  });
});

describe("fieldValue", () => {
  const state = { title: "x", pages: 10, durationMinutes: 90, episodeCount: 12 };
  it("returns value for known field", () => {
    expect(fieldValue(state, "title")).toBe("x");
    expect(fieldValue(state, "pages")).toBe(10);
    expect(fieldValue(state, "duration_minutes")).toBe(90);
    expect(fieldValue(state, "episode_count")).toBe(12);
  });
  it("returns undefined for unknown field", () => {
    expect(fieldValue(state, "unknown")).toBeUndefined();
  });
  it("returns undefined when key is missing on state", () => {
    expect(fieldValue({}, "title")).toBeUndefined();
  });
});

describe("fieldIsEmpty", () => {
  it("treats whitespace-only title as empty", () => {
    expect(fieldIsEmpty({ title: "   " }, "title")).toBe(true);
    expect(fieldIsEmpty({ title: "" }, "title")).toBe(true);
    expect(fieldIsEmpty({ title: null }, "title")).toBe(true);
    expect(fieldIsEmpty({ title: "x" }, "title")).toBe(false);
  });
  it("keeps zero as a non-empty numeric value", () => {
    expect(fieldIsEmpty({ pages: 0 }, "pages")).toBe(false);
    expect(fieldIsEmpty({ pages: 5 }, "pages")).toBe(false);
  });
  it("treats null and empty string as empty for non-trim fields", () => {
    expect(fieldIsEmpty({ pages: null }, "pages")).toBe(true);
    expect(fieldIsEmpty({ pages: "" }, "pages")).toBe(true);
    expect(fieldIsEmpty({ pages: undefined }, "pages")).toBe(true);
  });
  it("returns false for unknown field", () => {
    expect(fieldIsEmpty({}, "unknown")).toBe(false);
  });
});

describe("collectRequiredFields", () => {
  const byType = { book: ["pages"], film: ["duration_minutes"] };
  it("returns base list for workType", () => {
    expect(collectRequiredFields(byType, "book", "movie")).toEqual(["pages"]);
  });
  it("adds episode_count for tv_show", () => {
    expect(collectRequiredFields(byType, "film", "tv_show"))
      .toEqual(["duration_minutes", "episode_count"]);
  });
  it("does not add episode_count for movie", () => {
    expect(collectRequiredFields(byType, "film", "movie"))
      .toEqual(["duration_minutes"]);
  });
  it("returns empty for unknown workType", () => {
    expect(collectRequiredFields(byType, "game", "movie")).toEqual([]);
  });
  it("handles undefined requiredByType", () => {
    expect(collectRequiredFields(undefined, "book", "movie")).toEqual([]);
  });
  it("handles empty requiredByType entry", () => {
    expect(collectRequiredFields({}, "book", "movie")).toEqual([]);
  });
});

describe("isRequiredField", () => {
  const byType = { book: ["pages"], film: ["duration_minutes"] };
  it("true for base-required field", () => {
    expect(isRequiredField(
      { workType: "book", filmType: "movie" }, "pages", byType,
    )).toBe(true);
  });
  it("false for optional field", () => {
    expect(isRequiredField(
      { workType: "book", filmType: "movie" }, "description", byType,
    )).toBe(false);
  });
  it("respects tv_show extras", () => {
    expect(isRequiredField(
      { workType: "film", filmType: "tv_show" }, "episode_count", byType,
    )).toBe(true);
    expect(isRequiredField(
      { workType: "film", filmType: "movie" }, "episode_count", byType,
    )).toBe(false);
  });
});
