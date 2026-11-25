const SCRIPT_ID = "vor-domain-config";

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
    throw new Error(`Missing domain config element #${SCRIPT_ID}`);
  }
  const parsed = JSON.parse(el.textContent);
  if (!parsed || typeof parsed !== "object") {
    throw new Error(`Invalid domain config payload in #${SCRIPT_ID}`);
  }
  cachedConfig = parsed;
  return cachedConfig;
}
