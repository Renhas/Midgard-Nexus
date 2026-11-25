import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getStatusMixin } from "@vor/artworks/mixins/status";
import { resetDomainConfigCache } from "@vor/shared/domain";

describe("getStatusMixin", () => {
  beforeEach(() => {
    resetDomainConfigCache();
    const script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    script.textContent = JSON.stringify({
      statuses: {
        default: "st_a",
        completed: "st_done",
        options: [
          { value: "st_a", label: "State A" },
          { value: "st_b", label: "State B" },
        ],
      },
    });
    document.body.appendChild(script);
  });

  afterEach(() => {
    resetDomainConfigCache();
    document.body.innerHTML = "";
  });

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
