import { notify } from "@toast/notify";
import { formatHttpErrorToast } from "@toast/stack";

const DJANGO_LEVEL_MAP = {
  success: "success",
  error: "error",
  warning: "info",
  info: "info",
  debug: "info",
};

function parseToastFromTriggerHeader(rawHeader) {
  if (!rawHeader) {
    return null;
  }
  try {
    const parsed = JSON.parse(rawHeader);
    const toast = parsed && typeof parsed === "object" ? parsed["app:toast"] : null;
    return toast && typeof toast === "object" && toast.title ? toast : null;
  } catch {
    return null;
  }
}

export function handleHtmxAfterRequest(event) {
  const xhr = event?.detail?.xhr;
  if (!xhr) {
    return;
  }
  const toast = parseToastFromTriggerHeader(xhr.getResponseHeader?.("HX-Trigger"));
  if (toast) {
    notify.show(toast);
  }
}

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
  notify.error("Нет связи с сервером", {
    message: "Проверьте подключение к сети или состояние контейнера.",
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

document.body.addEventListener("htmx:afterRequest", handleHtmxAfterRequest);
document.body.addEventListener("htmx:responseError", handleHtmxResponseError);
document.body.addEventListener("htmx:sendError", handleHtmxSendError);

document.addEventListener("alpine:initialized", () => {
  flushDjangoMessages();
});
