import { beforeEach, describe, expect, it, vi } from "vitest";

const showMock = vi.fn();
const errorMock = vi.fn();

vi.mock("@toast/notify", () => ({
  notify: {
    show: showMock,
    error: errorMock,
  },
}));

const { handleHtmxToast, handleHtmxResponseError, handleHtmxSendError, flushDjangoMessages } =
  await import("@toast/bridge");

describe("Toast HTMX and Django messages bridge", () => {
  beforeEach(() => {
    showMock.mockClear();
    errorMock.mockClear();
    document.body.innerHTML = "";
  });

  it("forwards valid app:toast HTMX trigger payloads to notify.show", () => {
    handleHtmxToast({
      detail: {
        level: "success",
        title: "Сохранено",
        message: "Изменения применены",
      },
    });

    expect(showMock).toHaveBeenCalledWith({
      level: "success",
      title: "Сохранено",
      message: "Изменения применены",
    });
  });

  it("ignores malformed app:toast events without a title", () => {
    handleHtmxToast({ detail: { level: "info" } });
    expect(showMock).not.toHaveBeenCalled();
  });

  it("surfaces readable 400 plain-text/JSON errors without copy details", () => {
    handleHtmxResponseError({
      detail: {
        xhr: {
          status: 400,
          statusText: "Bad Request",
          responseText: "Недостаточно прав",
          getResponseHeader: () => "text/plain; charset=utf-8",
        },
        requestConfig: { verb: "post", path: "/library/1/edit/" },
      },
    });

    expect(errorMock).toHaveBeenCalledWith("Ошибка запроса (400)", {
      message: "Недостаточно прав",
      details: "",
    });
  });

  it("surfaces 500 HTML errors with generic message and copyable details", () => {
    handleHtmxResponseError({
      detail: {
        xhr: {
          status: 500,
          statusText: "Internal Server Error",
          responseText: "<!DOCTYPE html><html><body>ZeroDivisionError</body></html>",
          getResponseHeader: () => "text/html",
        },
        requestConfig: { verb: "post", path: "/library/add/" },
      },
    });

    expect(errorMock).toHaveBeenCalledTimes(1);
    const [title, opts] = errorMock.mock.calls[0];
    expect(title).toBe("Ошибка сервера (500)");
    expect(opts.message).toBe("Внутренняя ошибка сервера.");
    expect(opts.details).toContain("POST /library/add/ -> 500 Internal Server Error");
    expect(opts.details).toContain("ZeroDivisionError");
  });

  it("shows network error toast on htmx:sendError", () => {
    handleHtmxSendError();
    expect(errorMock).toHaveBeenCalledWith("Нет связи с сервером", {
      message: "Проверьте подключение к сети или состояние контейнера.",
    });
  });

  it("flushes serialized django.contrib.messages on init", () => {
    document.body.innerHTML = `<script id="app-django-messages" type="application/json">[{"level":"success","message":"Добро пожаловать"},{"level":"warning","message":"Внимание"}]</script>`;

    flushDjangoMessages();

    expect(showMock).toHaveBeenCalledTimes(2);
    expect(showMock).toHaveBeenNthCalledWith(1, { level: "success", title: "Добро пожаловать" });
    expect(showMock).toHaveBeenNthCalledWith(2, { level: "info", title: "Внимание" });
  });
});
