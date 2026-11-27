const VALID_LEVELS = new Set(["success", "error", "info"]);
const HTML_BODY_PATTERN = /<!doctype|<html|<body|<head/i;

export function readToastConfig(scriptId = "app-toast-config") {
  const el = typeof document !== "undefined" ? document.getElementById(scriptId) : null;
  if (!el?.textContent) {
    throw new Error(`Missing toast config element #${scriptId}`);
  }
  return normalizeToastConfig(JSON.parse(el.textContent));
}

export function normalizeToastConfig(raw) {
  const src = raw && typeof raw === "object" ? raw : {};
  const maxVisible = Number(src.maxVisible);
  const duration = Number(src.duration);
  const errorDuration = Number(src.errorDuration);
  if (!Number.isFinite(maxVisible) || maxVisible < 1) {
    throw new Error("Invalid toast config: maxVisible");
  }
  if (!Number.isFinite(duration) || duration < 0) {
    throw new Error("Invalid toast config: duration");
  }
  if (!Number.isFinite(errorDuration) || errorDuration < 0) {
    throw new Error("Invalid toast config: errorDuration");
  }
  return {
    maxVisible: Math.floor(maxVisible),
    duration,
    errorDuration,
  };
}

export function normalizeToastLevel(level) {
  const normalized = String(level || "info").toLowerCase();
  return VALID_LEVELS.has(normalized) ? normalized : "info";
}

export function resolveToastDuration(level, explicitDuration, config) {
  if (explicitDuration !== undefined && explicitDuration !== null) {
    const num = Number(explicitDuration);
    if (Number.isFinite(num) && num >= 0) {
      return num;
    }
  }
  return level === "error" ? config.errorDuration : config.duration;
}

export function createToastEntry(payload, id, config) {
  const data = typeof payload === "string" ? { title: payload } : payload || {};
  const level = normalizeToastLevel(data.level);
  const duration = resolveToastDuration(level, data.duration, config);
  const action =
    data.action && typeof data.action === "object" && data.action.label
      ? {
          label: String(data.action.label),
          onClick: typeof data.action.onClick === "function" ? data.action.onClick : null,
          event: data.action.event ? String(data.action.event) : "",
          detail: data.action.detail ?? null,
        }
      : null;

  return {
    id,
    level,
    title: String(data.title || "").trim(),
    message: String(data.message || "").trim(),
    details: data.details ? String(data.details) : "",
    duration,
    action,
    copied: false,
    closing: false,
  };
}

export function computeStackSlots(items, maxVisible) {
  const list = items || [];
  const visible = Number.isFinite(maxVisible) && maxVisible >= 1 ? list.slice(-maxVisible) : list;
  const total = visible.length;
  return visible.map((item, idx) => ({
    ...item,
    stackIndex: total - 1 - idx,
  }));
}

export function isHtmlPayload(rawBody, contentType = "") {
  return (
    String(contentType || "")
      .toLowerCase()
      .includes("text/html") || HTML_BODY_PATTERN.test(String(rawBody || ""))
  );
}

export function extractErrorMessage(rawBody, contentType = "", fallback = "Ошибка запроса") {
  const text = String(rawBody || "").trim();
  if (!text) {
    return fallback;
  }
  const lowerType = String(contentType || "").toLowerCase();
  if (lowerType.includes("application/json") || text.startsWith("{")) {
    try {
      const parsed = JSON.parse(text);
      const allErrors = parsed?.errors?.__all__;
      const firstAll = Array.isArray(allErrors) ? allErrors[0] : allErrors;
      const candidates = [parsed?.error, parsed?.message, firstAll, firstAll?.message];
      const found = candidates.find((item) => typeof item === "string" && item.trim());
      if (found) {
        return found.trim();
      }
    } catch {
      // fall through to plain-text check
    }
  }
  if (isHtmlPayload(text, lowerType)) {
    return fallback;
  }
  return text;
}
