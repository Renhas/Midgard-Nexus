const SCRIPT_ID = "vor-domain-config";

const EMPTY_CONFIG = Object.freeze({
  workTypes: { keys: [], default: "", items: [] },
  filmTypes: { default: "", options: [] },
  statuses: { default: "", completed: "", options: [] },
  ageRatings: { options: [] },
  relations: { default: "", types: [] },
  rating: { min: 1, max: 10 },
  validation: {
    requiredByType: {},
    conditionalRequired: [],
    fieldToState: {},
    draftLabels: {},
  },
});

let cachedConfig = null;

export function resetDomainConfigCache() {
  cachedConfig = null;
}

export function getDomainConfig() {
  if (cachedConfig !== null) {
    return cachedConfig;
  }
  const el = typeof document !== "undefined" ? document.getElementById(SCRIPT_ID) : null;
  if (!el || !el.textContent) {
    return EMPTY_CONFIG;
  }
  try {
    const parsed = JSON.parse(el.textContent);
    if (parsed && typeof parsed === "object") {
      cachedConfig = parsed;
      return cachedConfig;
    }
  } catch (error) {
    // Fallback to EMPTY_CONFIG when JSON is malformed
  }
  return EMPTY_CONFIG;
}
