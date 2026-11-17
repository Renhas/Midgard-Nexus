export const FIELD_TO_STATE = {
  title: { key: "title", trim: true },
  pages: { key: "pages" },
  duration_minutes: { key: "durationMinutes" },
  episode_count: { key: "episodeCount" },
};

export function fieldValue(state, name) {
  const spec = FIELD_TO_STATE[name];
  if (!spec) {
    return undefined;
  }
  return state[spec.key];
}

export function fieldIsEmpty(state, name) {
  const spec = FIELD_TO_STATE[name];
  if (!spec) {
    return false;
  }
  const value = state[spec.key];
  if (spec.trim) {
    return !String(value || "").trim();
  }
  return value === "" || value == null;
}

export function collectRequiredFields(requiredByType, workType, filmType) {
  const base = (requiredByType && requiredByType[workType]) || [];
  const extras = workType === "film" && filmType === "tv_show" ? ["episode_count"] : [];
  return [...base, ...extras];
}

export function isRequiredField(state, name, requiredByType) {
  return collectRequiredFields(requiredByType, state.workType, state.filmType).includes(name);
}
