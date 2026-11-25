import { afterEach, beforeEach, vi } from "vitest";
import { resetDomainConfigCache } from "@vor/shared/domain";

const TEST_DOMAIN_CONFIG = {
  workTypes: { keys: ["type_a", "type_b"], default: "type_a", items: [] },
  filmTypes: { default: "sub_default", options: [] },
  statuses: {
    default: "st_a",
    completed: "st_done",
    options: [
      { value: "st_a", label: "State A" },
      { value: "st_b", label: "State B" },
    ],
  },
  ageRatings: { options: [] },
  relations: { default: "rel_any", types: [] },
  rating: { min: 1, max: 10 },
  validation: {
    requiredByType: {},
    conditionalRequired: [],
    fieldToState: {},
    draftLabels: {},
  },
};

export function setDomainConfig(overrides = {}) {
  resetDomainConfigCache();
  let script = document.getElementById("vor-domain-config");
  if (!script) {
    script = document.createElement("script");
    script.id = "vor-domain-config";
    script.type = "application/json";
    document.body.appendChild(script);
  }
  script.textContent = JSON.stringify({ ...TEST_DOMAIN_CONFIG, ...overrides });
}

beforeEach(() => {
  setDomainConfig();
});

afterEach(() => {
  resetDomainConfigCache();
  document.getElementById("vor-domain-config")?.remove();
});

if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (!globalThis.IntersectionObserver) {
  globalThis.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
