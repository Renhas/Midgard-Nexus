export function fieldValue(state, name, fieldToState = {}) {
  const spec = fieldToState[name];
  if (!spec) {
    return undefined;
  }
  return state[spec.key];
}

export function fieldIsEmpty(state, name, fieldToState = {}) {
  const spec = fieldToState[name];
  if (!spec) {
    return false;
  }
  const value = state[spec.key];
  if (spec.trim) {
    return !String(value || "").trim();
  }
  return value === "" || value == null;
}

function matchesCondition(state, when) {
  if (!when || typeof when !== "object") {
    return false;
  }
  return Object.entries(when).every(([key, expected]) => state[key] === expected);
}

export function collectRequiredFields(state, validationConfig = {}) {
  const requiredByType = validationConfig.requiredByType || {};
  const conditionalRequired = validationConfig.conditionalRequired || [];
  const base = requiredByType[state.workType] || [];
  const extras = conditionalRequired
    .filter((rule) => rule.workType === state.workType && matchesCondition(state, rule.when))
    .flatMap((rule) => rule.fields || []);
  return [...base, ...extras];
}

export function isRequiredField(state, name, validationConfig = {}) {
  return collectRequiredFields(state, validationConfig).includes(name);
}
