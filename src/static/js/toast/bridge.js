import { notify } from "@toast/notify";
import { extractErrorMessage } from "@toast/stack";

const DJANGO_LEVEL_MAP = {
  success: "success",
  error: "error",
  warning: "info",
  info: "info",
  debug: "info",
};

function statusTitle(status) {
  if (!status) {
    return "Ошибка запроса";
  }
  if (status >= 500) {
    return `Ошибка сервера (${status})`;
  }
  if (status === 403) {
    return "Доступ запрещён";
  }
  if (status === 404) {
    return "Не найдено (404)";
  }
  return `Ошибка запроса (${status})`;
}

function buildHttpDetails(xhr, requestConfig) {
  if (!xhr) {
    return "";
  }
  const method = String(requestConfig?.verb || "HTTP").toUpperCase();
  const url = requestConfig?.path || xhr.responseURL || "";
  const statusLine = `${method} ${url} -> ${xhr.status} ${xhr.statusText || ""}`.trim();
  const body = String(xhr.responseText || "").trim();
  if (!body) {
    return statusLine;
  }
  const clipped = body.length > 4000 ? `${body.slice(0, 4000)}\n...[truncated]` : body;
  return `${statusLine}\n\n${clipped}`;
}

export function handleHtmxToast(event) {
  const detail = event?.detail;
  if (!detail) {
    return;
  }
  const payload = detail.value !== undefined && typeof detail.value === "object" ? detail.value : detail;
  if (!payload || typeof payload !== "object" || !payload.title) {
    return;
  }
  notify.show(payload);
}

export function handleHtmxResponseError(event) {
  const xhr = event?.detail?.xhr;
  if (!xhr) {
    return;
  }
  const status = Number(xhr.status || 0);
  const contentType = xhr.getResponseHeader?.("Content-Type") || "";
  const fallback = status >= 500 ? "Внутренняя ошибка сервера." : "";
  const extracted = extractErrorMessage(xhr.responseText, contentType, fallback);

  const isServerOrHtml =
    status >= 500 ||
    contentType.toLowerCase().includes("text/html") ||
    /<!doctype|<html|<body|<head/i.test(String(xhr.responseText || ""));

  notify.error(statusTitle(status), {
    message: extracted,
    details: isServerOrHtml ? buildHttpDetails(xhr, event?.detail?.requestConfig) : "",
  });
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
    notify.show({
      level,
      title: text,
    });
  });
}

document.body.addEventListener("app:toast", handleHtmxToast);
document.body.addEventListener("htmx:responseError", handleHtmxResponseError);
document.body.addEventListener("htmx:sendError", handleHtmxSendError);

document.addEventListener("alpine:initialized", () => {
  flushDjangoMessages();
});
