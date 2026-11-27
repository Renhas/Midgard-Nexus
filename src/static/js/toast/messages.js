import { extractErrorMessage, isHtmlPayload } from "@toast/stack";

const MAX_ERROR_DETAILS_LENGTH = 4000;

export const TOAST_MESSAGES = {
  networkError: {
    title: "Нет связи с сервером",
    message: "Проверьте подключение к сети или состояние контейнера.",
  },
  defaultRequestError: "Ошибка запроса",
  serverErrorFallback: "Внутренняя ошибка сервера.",
  statusTitles: {
    403: "Доступ запрещён",
    404: "Не найдено (404)",
  },
};

export function httpStatusTitle(status) {
  const code = Number(status || 0);
  if (!code) {
    return TOAST_MESSAGES.defaultRequestError;
  }
  if (TOAST_MESSAGES.statusTitles[code]) {
    return TOAST_MESSAGES.statusTitles[code];
  }
  return code >= 500 ? `Ошибка сервера (${code})` : `Ошибка запроса (${code})`;
}

export function buildHttpDetails({ method = "HTTP", url = "", status = 0, statusText = "", body = "" } = {}) {
  const statusLine = `${String(method).toUpperCase()} ${url} -> ${status} ${statusText}`.trim();
  const trimmedBody = String(body || "").trim();
  if (!trimmedBody) {
    return statusLine;
  }
  const clipped =
    trimmedBody.length > MAX_ERROR_DETAILS_LENGTH
      ? `${trimmedBody.slice(0, MAX_ERROR_DETAILS_LENGTH)}\n...[truncated]`
      : trimmedBody;
  return `${statusLine}\n\n${clipped}`;
}

export function formatHttpErrorToast({
  method = "HTTP",
  url = "",
  status = 0,
  statusText = "",
  contentType = "",
  body = "",
} = {}) {
  const code = Number(status || 0);
  const fallback = code >= 500 ? TOAST_MESSAGES.serverErrorFallback : "";
  const message = extractErrorMessage(body, contentType, fallback);
  const needsDetails = code >= 500 || isHtmlPayload(body, contentType);
  return {
    title: httpStatusTitle(code),
    message,
    details: needsDetails ? buildHttpDetails({ method, url, status: code, statusText, body }) : "",
  };
}
