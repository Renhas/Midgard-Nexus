const VALID_LEVELS = new Set(["success", "error", "info"]);

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
  const data = typeof payload === "string" ? { message: payload } : payload || {};
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

export function extractErrorMessage(rawBody, contentType = "", fallback = "Ошибка запроса") {
  const text = String(rawBody || "").trim();
  if (!text) {
    return fallback;
  }
  const lowerType = String(contentType || "").toLowerCase();
  if (lowerType.includes("application/json") || text.startsWith("{")) {
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed?.error === "string" && parsed.error.trim()) {
        return parsed.error.trim();
      }
      if (typeof parsed?.message === "string" && parsed.message.trim()) {
        return parsed.message.trim();
      }
      const firstAll = parsed?.errors?.__all__?.[0];
      if (typeof firstAll === "string" && firstAll.trim()) {
        return firstAll.trim();
      }
      if (typeof firstAll?.message === "string" && firstAll.message.trim()) {
        return firstAll.message.trim();
      }
    } catch {
      // fall through to plain-text check
    }
  }
  if (lowerType.includes("text/html") || /<!doctype|<html|<body|<head/i.test(text)) {
    return fallback;
  }
  return text;
}
