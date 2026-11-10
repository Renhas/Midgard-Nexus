import { describe, expect, it } from "vitest";
import {
  serializeDraft,
  parseDraft,
  dirtyChanges,
} from "@vor/artworks/pure/draft";

function makeSource() {
  return {
    title: "T",
    description: "D",
    releaseDate: "2024-01-01",
    ageRating: "12+",
    externalLink: "",
    pages: 10,
    durationMinutes: "",
    episodeCount: "",
    authors: [{ id: 1 }],
    genres: [],
    tags: [],
    platforms: [],
    relations: [],
    coverPreview: "/x.jpg",
    coverCleared: false,
    coverFile: null,
  };
}

describe("serializeDraft", () => {
  it("serializes all fields", () => {
    const json = serializeDraft(makeSource());
    const data = JSON.parse(json);
    expect(data.title).toBe("T");
    expect(data.pages).toBe(10);
    expect(data.authors).toEqual([{ id: 1 }]);
    expect(data.coverName).toBe("");
    expect(data.coverCleared).toBe(false);
  });
  it("captures cover file name", () => {
    const source = makeSource();
    source.coverFile = { name: "cover.jpg" };
    const data = JSON.parse(serializeDraft(source));
    expect(data.coverName).toBe("cover.jpg");
  });
  it("omits cover file content", () => {
    const source = makeSource();
    source.coverFile = { name: "cover.jpg", size: 12345 };
    const data = JSON.parse(serializeDraft(source));
    expect(Object.keys(data)).not.toContain("coverFile");
  });
});

describe("parseDraft", () => {
  it("parses valid json", () => {
    expect(parseDraft('{"a":1}')).toEqual({ a: 1 });
  });
  it("returns {} for empty input", () => {
    expect(parseDraft("")).toEqual({});
    expect(parseDraft(null)).toEqual({});
    expect(parseDraft(undefined)).toEqual({});
  });
  it("returns {} for malformed json", () => {
    expect(parseDraft("not-json")).toEqual({});
    expect(parseDraft('{"a":')).toEqual({});
  });
  it("round-trips serializeDraft", () => {
    const source = makeSource();
    expect(parseDraft(serializeDraft(source)).title).toBe("T");
  });
});

describe("dirtyChanges", () => {
  const labels = {
    title: "Название",
    description: "Описание",
    authors: "Авторы",
  };

  it("returns empty for identical snapshots", () => {
    expect(dirtyChanges({ title: "a" }, { title: "a" }, labels, false))
      .toEqual([]);
  });
  it("detects scalar change", () => {
    expect(dirtyChanges({ title: "a" }, { title: "b" }, labels, false))
      .toEqual(["Название"]);
  });
  it("treats missing key as empty string", () => {
    expect(dirtyChanges({}, { title: "b" }, labels, false))
      .toEqual(["Название"]);
    expect(dirtyChanges({ title: "b" }, {}, labels, false))
      .toEqual(["Название"]);
  });
  it("detects array change", () => {
    expect(dirtyChanges({ authors: [{ id: 1 }] }, { authors: [{ id: 2 }] }, labels, false))
      .toEqual(["Авторы"]);
  });
  it("treats equal arrays as no change", () => {
    expect(dirtyChanges({ authors: [{ id: 1 }] }, { authors: [{ id: 1 }] }, labels, false))
      .toEqual([]);
  });
  it("appends cover change when flag is set", () => {
    expect(dirtyChanges({}, {}, labels, true)).toEqual(["Обложка"]);
  });
  it("does not append cover when flag is false", () => {
    expect(dirtyChanges({ title: "a" }, { title: "b" }, labels, false))
      .toEqual(["Название"]);
  });
  it("only checks labeled keys", () => {
    expect(dirtyChanges({ title: "a", other: 1 }, { title: "a", other: 2 }, labels, false))
      .toEqual([]);
  });
});
