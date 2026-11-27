import { notify } from "@toast/notify";
import { TOAST_MESSAGES, formatHttpErrorToast } from "@toast/messages";

const DJANGO_LEVEL_MAP = {
  success: "success",
  error: "error",
  warning: "info",
  info: "info",
  debug: "info",
};

export function handleHtmxResponseError(event) {
  const xhr = event?.detail?.xhr;
  if (!xhr) {
    return;
  }
  const requestConfig = event?.detail?.requestConfig;
  const { title, message, details } = formatHttpErrorToast({
    method: requestConfig?.verb || "HTTP",
    url: requestConfig?.path || xhr.responseURL || "",
    status: xhr.status,
    statusText: xhr.statusText,
    contentType: xhr.getResponseHeader?.("Content-Type") || "",
    body: xhr.responseText,
  });
  notify.error(title, { message, details });
}

export function handleHtmxSendError() {
  notify.error(TOAST_MESSAGES.networkError.title, {
    message: TOAST_MESSAGES.networkError.message,
  });
}

export function flushDjangoMessages(scriptId = "app-django-messages") {
  const el = document.getElementById(scriptId);
  if (!el?.textContent) {
    return;
  }
  let items;
  try {
    items = JSON.parse(el.textContent);
  } catch {
    return;
  }
  if (!Array.isArray(items)) {
    return;
  }
  items.forEach((item) => {
    const text = String(item?.message || "").trim();
    if (!text) {
      return;
    }
    const level = DJANGO_LEVEL_MAP[String(item?.level || "").toLowerCase()] || "info";
    notify.show({ level, title: text });
  });
}

document.body.addEventListener("htmx:responseError", handleHtmxResponseError);
document.body.addEventListener("htmx:sendError", handleHtmxSendError);

document.addEventListener("alpine:initialized", () => {
  flushDjangoMessages();
});
