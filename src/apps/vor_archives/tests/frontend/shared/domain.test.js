import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getDomainConfig, resetDomainConfigCache } from "@vor/shared/domain";

describe("getDomainConfig", () => {
  beforeEach(() => {
    resetDomainConfigCache();
    document.body.innerHTML = "";
  });

  afterEach(() => {
    resetDomainConfigCache();
    document.body.innerHTML = "";
  });

  it("returns safe empty fallback when script tag is missing", () => {
    const cfg = getDomainConfig();
    expect(cfg.workTypes.keys).toEqual([]);
    expect(cfg.relations.types).toEqual([]);
    expect(cfg.validation.requiredByType).toEqual({});
  });

  it("parses and caches JSON from #vor-domain-config", () => {
    const script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    script.textContent = JSON.stringify({
      workTypes: { keys: ["book"], default: "book", items: [] },
      statuses: { default: "planning", completed: "completed", options: [] },
    });
    document.body.appendChild(script);

    const first = getDomainConfig();
    expect(first.workTypes.keys).toEqual(["book"]);
    expect(first.statuses.default).toBe("planning");

    script.remove();
    const second = getDomainConfig();
    expect(second).toBe(first);
  });

  it("returns fallback when JSON is invalid", () => {
    const script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    script.textContent = "{broken json";
    document.body.appendChild(script);

    const cfg = getDomainConfig();
    expect(cfg.workTypes.keys).toEqual([]);
  });
});
