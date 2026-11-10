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

async function requestJson(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...getCsrfHeaders(),
        ...(options.headers || {}),
      },
    });
    try {
      return await response.json();
    } catch (parseError) {
      return null;
    }
  } catch (networkError) {
    return null;
  }
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

function postForm(url, payload) {
  return requestJson(url, {
    method: "POST",
    body: urlencoded(payload),
  });
}

export const VorApi = {
  quickUpdate(quickUrl, field, value) {
    return postForm(quickUrl, { field, value });
  },
  saveWork(saveUrl, formData) {
    return requestJson(saveUrl, { method: "POST", body: formData });
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
    return requestJson(
      `${relationSearchUrl}?${new URLSearchParams(params).toString()}`,
    );
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
