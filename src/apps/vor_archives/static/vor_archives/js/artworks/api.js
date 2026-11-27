/**
 * VorApi - единый слой JSON-запросов для страницы artworks.
 *
 * Сюда попадают только fetch + JSON. Всё, что отдаёт HTML для swap,
 * остаётся на htmx.ajax.
 *
 * Контракт: методы никогда не бросают исключений. При сетевой ошибке
 * или не-JSON ответе возвращают null. Caller проверяет data?.ok.
 */
import { getCsrfHeaders } from "@vor/shared/csrf";
import { notify } from "@toast/notify";
import { formatHttpErrorToast } from "@toast/stack";

async function requestJson(url, options = {}) {
  const { silent = false, ...fetchOptions } = options;
  const method = String(fetchOptions.method || "GET").toUpperCase();
  let response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers: {
        ...getCsrfHeaders(),
        ...(fetchOptions.headers || {}),
      },
    });
  } catch {
    notify.error("Нет связи с сервером", {
      message: "Проверьте подключение к сети или состояние контейнера.",
    });
    return null;
  }

  const contentType = response.headers.get("Content-Type") || "";
  const rawBody = await response.text();
  let parsed = null;
  if (rawBody) {
    try {
      parsed = JSON.parse(rawBody);
    } catch {
      parsed = null;
    }
  }

  if (!response.ok) {
    if (!silent || response.status >= 500 || parsed === null) {
      const { title, message, details } = formatHttpErrorToast({
        method,
        url,
        status: response.status,
        statusText: response.statusText,
        contentType,
        body: rawBody,
      });
      notify.error(title, { message, details });
    }
    return parsed;
  }

  return parsed;
}

function urlencoded(payload) {
  const body = new URLSearchParams();
  Object.entries(payload || {}).forEach(([key, value]) => {
    if (value == null) {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => body.append(key, String(item)));
      return;
    }
    body.set(key, String(value));
  });
  return body;
}

function postForm(url, payload, options = {}) {
  return requestJson(url, {
    ...options,
    method: "POST",
    body: urlencoded(payload),
  });
}

export const VorApi = {
  quickUpdate(quickUrl, field, value) {
    return postForm(quickUrl, { field, value });
  },
  saveWork(saveUrl, formData) {
    return requestJson(saveUrl, { method: "POST", body: formData, silent: true });
  },
  attachWork(attachUrl, payload) {
    return postForm(attachUrl, payload);
  },
  attachWorkFromSearch(attachUrl, typeKey, workId) {
    return postForm(attachUrl, {
      work_type: typeKey,
      work_id: workId,
      status: "planning",
    });
  },
  searchRelatedWorks(relationSearchUrl, params) {
    return requestJson(`${relationSearchUrl}?${new URLSearchParams(params).toString()}`);
  },
  listArtworkCollections(listUrl, uwId) {
    return requestJson(`${listUrl}${uwId}/collections/`);
  },
  addWorkToCollection(itemsUrl, uwId) {
    return postForm(itemsUrl, { uw_id: uwId, action: "add" });
  },
  removeWorkFromCollection(itemsUrl, uwId) {
    return postForm(itemsUrl, { uw_id: uwId, action: "remove" });
  },
  toggleWorkCollection(itemsUrl, uwId, adding) {
    return postForm(itemsUrl, {
      uw_id: uwId,
      action: adding ? "add" : "remove",
    });
  },
  moveCollection(reorderUrl, payload) {
    return postForm(reorderUrl, {
      id: payload.id,
      parent_id: payload.parent_id,
      sibling_ids: payload.sibling_ids || [],
    });
  },
  saveWorkOrder(reorderUrl, ids) {
    return postForm(reorderUrl, { ids });
  },
};

export default VorApi;
