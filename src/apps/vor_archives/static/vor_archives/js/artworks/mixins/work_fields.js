export const BASE_DEFAULTS = {
  workType: "",
  filmType: "movie",
  title: "",
  description: "",
  releaseDate: "",
  externalLink: "",
  ageRating: "",
  pages: "",
  durationMinutes: "",
  episodeCount: "",
  authors: [],
  genres: [],
  tags: [],
  platforms: [],
};

export const WORK_FIELD_KEYS = Object.keys(BASE_DEFAULTS);

function cloneValue(value) {
  return Array.isArray(value) ? value.slice() : value;
}

function cloneFields(source) {
  const out = {};
  WORK_FIELD_KEYS.forEach((key) => {
    out[key] = cloneValue(source[key]);
  });
  return out;
}

export function getWorkFieldsMixin(source = {}) {
  const initial = {};
  WORK_FIELD_KEYS.forEach((key) => {
    initial[key] = cloneValue(source[key] ?? BASE_DEFAULTS[key]);
  });
  return {
    ...cloneFields(initial),
    applyWorkFields(data) {
      WORK_FIELD_KEYS.forEach((key) => {
        if (data[key] !== undefined) {
          this[key] = cloneValue(data[key]);
        }
      });
    },
    resetWorkFields() {
      WORK_FIELD_KEYS.forEach((key) => {
        this[key] = cloneValue(initial[key]);
      });
    },
    workFieldsSnapshot() {
      const out = {};
      WORK_FIELD_KEYS.forEach((key) => {
        out[key] = this[key];
      });
      return out;
    },
  };
}
