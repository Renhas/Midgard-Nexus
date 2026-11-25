import { describe, expect, it, vi } from "vitest";
import { getStatusMixin } from "@vor/artworks/mixins/status";

describe("getStatusMixin", () => {
  it("uses default status and options from domain config", () => {
    const ctx = getStatusMixin();
    expect(ctx.status).toBe("st_a");
    expect(ctx.statusLabel()).toBe("State A");
  });

  it("updates status optimistically and delegates side-effects to saveField", () => {
    const saveField = vi.fn();
    const ctx = {
      progress: 42,
      progressMax: 100,
      saveField,
      ...getStatusMixin({ status: "st_a" }),
    };

    ctx.setStatus("st_b");

    expect(ctx.status).toBe("st_b");
    expect(ctx.progress).toBe(42);
    expect(saveField).toHaveBeenCalledWith("status", "st_b");
  });

  it("does not trigger saveField when selecting current status", () => {
    const saveField = vi.fn();
    const ctx = {
      saveField,
      ...getStatusMixin({ status: "st_a" }),
    };

    ctx.setStatus("st_a");

    expect(saveField).not.toHaveBeenCalled();
  });
});
