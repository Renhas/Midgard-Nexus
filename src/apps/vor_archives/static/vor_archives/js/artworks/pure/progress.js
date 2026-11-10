export function progressValueLabel(value) {
  const v = Number(value || 0);
  return v === Math.round(v)
    ? String(Math.round(v))
    : String(Math.round(v * 10) / 10);
}

export function progressSuffix(progressMax, progressUnit) {
  if (progressMax != null) {
    return `/${progressMax} ${progressUnit || ""}`.trim();
  }
  return progressUnit || "";
}

export function progressCh(progressMax) {
  if (progressMax != null) {
    return String(Math.floor(progressMax)).length;
  }
  return 4;
}

export function clampProgress(value, progressMax) {
  let next = Math.max(0, value);
  if (progressMax != null) {
    next = Math.min(progressMax, next);
  }
  return Math.round(next * 10) / 10;
}

export function parseProgressDraft(draft) {
  const raw = String(draft).replace(",", ".");
  const parsed = Number(raw);
  return Number.isNaN(parsed) ? null : parsed;
}
