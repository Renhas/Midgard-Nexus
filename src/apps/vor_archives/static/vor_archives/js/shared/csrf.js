import { readCookie } from "@vor/shared/pure/cookies";

function csrfTokenFromDom() {
  return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

export function getCsrfToken() {
  return csrfTokenFromDom() || readCookie(document.cookie, "csrftoken") || "";
}

export function getCsrfHeaders() {
  return {
    "X-CSRFToken": getCsrfToken(),
    "X-Requested-With": "XMLHttpRequest"
  };
}

document.body.addEventListener("htmx:configRequest", (event) => {
  const token = getCsrfToken();
  if (token) {
    event.detail.headers["X-CSRFToken"] = token;
  }
});
