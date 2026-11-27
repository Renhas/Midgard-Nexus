import { beforeEach, describe, expect, it, vi } from "vitest";
import { TOAST_MESSAGES, httpStatusTitle } from "@toast/messages";

const showMock = vi.fn();
const errorMock = vi.fn();

vi.mock("@toast/notify", () => ({
  notify: {
    show: showMock,
    error: errorMock,
  },
}));

const { handleHtmxResponseError, handleHtmxSendError, flushDjangoMessages } = await import("@toast/bridge");

describe("Toast HTMX and Django messages bridge", () => {
  beforeEach(() => {
    showMock.mockClear();
    errorMock.mockClear();
    document.body.innerHTML = "";
  });

  it("surfaces readable 400 plain-text errors without copy details", () => {
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

    expect(errorMock).toHaveBeenCalledWith(httpStatusTitle(400), {
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
    expect(title).toBe(httpStatusTitle(500));
    expect(opts.message).toBe(TOAST_MESSAGES.serverErrorFallback);
    expect(opts.details).toContain("POST /library/add/ -> 500 Internal Server Error");
    expect(opts.details).toContain("ZeroDivisionError");
  });

  it("shows network error toast on htmx:sendError", () => {
    handleHtmxSendError();
    expect(errorMock).toHaveBeenCalledWith(TOAST_MESSAGES.networkError.title, {
      message: TOAST_MESSAGES.networkError.message,
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
