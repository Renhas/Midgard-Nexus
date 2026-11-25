import { describe, expect, it, vi } from "vitest";
import { getStatusMixin } from "@vor/artworks/mixins/status";

describe("getStatusMixin", () => {
  const choices = [
    { value: "st_a", label: "State A" },
    { value: "st_b", label: "State B" },
  ];

  it("updates status optimistically and delegates side-effects to saveField", () => {
    const saveField = vi.fn();
    const ctx = {
      progress: 42,
      progressMax: 100,
      saveField,
      ...getStatusMixin({ status: "st_a", choices }),
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
      ...getStatusMixin({ status: "st_a", choices }),
    };

    ctx.setStatus("st_a");

    expect(saveField).not.toHaveBeenCalled();
  });
});
