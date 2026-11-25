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

  it("throws when script tag is missing", () => {
    expect(() => getDomainConfig()).toThrow(/vor-domain-config/);
  });

  it("parses and caches JSON from #vor-domain-config", () => {
    const script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    script.textContent = JSON.stringify({
      workTypes: { keys: ["type_a"], default: "type_a", items: [] },
      statuses: { default: "st_a", completed: "st_done", options: [] },
    });
    document.body.appendChild(script);

    const first = getDomainConfig();
    expect(first.workTypes.keys).toEqual(["type_a"]);
    expect(first.statuses.default).toBe("st_a");

    script.remove();
    const second = getDomainConfig();
    expect(second).toBe(first);
  });

  it("throws when JSON is malformed", () => {
    const script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    script.textContent = "{broken json";
    document.body.appendChild(script);

    expect(() => getDomainConfig()).toThrow();
  });
});
