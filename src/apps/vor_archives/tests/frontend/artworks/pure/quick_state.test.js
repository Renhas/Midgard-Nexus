import { describe, expect, it } from "vitest";
import {
  captureQuickState,
  restoreQuickState,
  applyQuickResult,
} from "@vor/artworks/pure/quick_state";

function makeSource() {
  return {
    status: "watching",
    rating: 7,
    progress: 5,
    isHidden: true,
    timesCompleted: 2,
    ownedPlatformIds: [1, 2],
    lastCompletedDate: "2024-01-01",
  };
}

describe("captureQuickState", () => {
  it("copies all quick fields", () => {
    expect(captureQuickState(makeSource())).toEqual({
      status: "watching",
      rating: 7,
      progress: 5,
      isHidden: true,
      timesCompleted: 2,
      ownedPlatformIds: [1, 2],
      lastCompletedDate: "2024-01-01",
    });
  });
  it("clones ownedPlatformIds", () => {
    const source = makeSource();
    const snap = captureQuickState(source);
    expect(snap.ownedPlatformIds).not.toBe(source.ownedPlatformIds);
  });
  it("handles undefined ownedPlatformIds", () => {
    const source = { ...makeSource(), ownedPlatformIds: undefined };
    expect(captureQuickState(source).ownedPlatformIds).toEqual([]);
  });
});

describe("restoreQuickState", () => {
  it("restores all fields", () => {
    const target = {};
    restoreQuickState(target, {
      status: "done",
      rating: 9,
      progress: 10,
      isHidden: false,
      timesCompleted: 3,
      ownedPlatformIds: [5],
      lastCompletedDate: "2024-02-02",
    });
    expect(target).toEqual({
      status: "done",
      rating: 9,
      progress: 10,
      isHidden: false,
      timesCompleted: 3,
      ownedPlatformIds: [5],
      lastCompletedDate: "2024-02-02",
    });
  });
  it("no-op on null snap", () => {
    const target = { status: "x" };
    restoreQuickState(target, null);
    expect(target.status).toBe("x");
  });
  it("no-op on undefined snap", () => {
    const target = { status: "x" };
    restoreQuickState(target, undefined);
    expect(target.status).toBe("x");
  });
});

describe("applyQuickResult", () => {
  it("updates status if present", () => {
    const target = {};
    applyQuickResult(target, { status: "done" });
    expect(target.status).toBe("done");
  });
  it("ignores empty status", () => {
    const target = { status: "watching" };
    applyQuickResult(target, { status: "" });
    expect(target.status).toBe("watching");
  });
  it("updates progress via Number", () => {
    const target = {};
    applyQuickResult(target, { progress: "3.5" });
    expect(target.progress).toBe(3.5);
  });
  it("ignores null progress", () => {
    const target = { progress: 1 };
    applyQuickResult(target, { progress: null });
    expect(target.progress).toBe(1);
  });
  it("updates times_completed via Number", () => {
    const target = {};
    applyQuickResult(target, { times_completed: "2" });
    expect(target.timesCompleted).toBe(2);
  });
  it("updates last_completed_date when key present (null -> empty)", () => {
    const target = { lastCompletedDate: "2024-01-01" };
    applyQuickResult(target, { last_completed_date: null });
    expect(target.lastCompletedDate).toBe("");
  });
  it("ignores missing last_completed_date key", () => {
    const target = { lastCompletedDate: "2024-01-01" };
    applyQuickResult(target, {});
    expect(target.lastCompletedDate).toBe("2024-01-01");
  });
  it("converts owned_platform_ids to numbers", () => {
    const target = {};
    applyQuickResult(target, { owned_platform_ids: ["1", "2"] });
    expect(target.ownedPlatformIds).toEqual([1, 2]);
  });
  it("ignores non-array owned_platform_ids", () => {
    const target = { ownedPlatformIds: [1] };
    applyQuickResult(target, { owned_platform_ids: "1,2" });
    expect(target.ownedPlatformIds).toEqual([1]);
  });
  it("no-op on null data", () => {
    const target = { status: "x" };
    applyQuickResult(target, null);
    expect(target.status).toBe("x");
  });
  it("no-op on non-object data", () => {
    const target = { status: "x" };
    applyQuickResult(target, "string");
    expect(target.status).toBe("x");
  });
});
