import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TOAST_MESSAGES, httpStatusTitle } from "@toast/messages";

const errorMock = vi.fn();

vi.mock("@toast/notify", () => ({
  notify: {
    error: errorMock,
  },
}));

const { VorApi } = await import("@vor/artworks/api");

describe("VorApi error notifications", () => {
  beforeEach(() => {
    errorMock.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows network error toast and returns null when fetch rejects", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new TypeError("Failed to fetch"));

    const result = await VorApi.quickUpdate("/library/1/quick/", "rating", 8);

    expect(result).toBeNull();
    expect(errorMock).toHaveBeenCalledWith(TOAST_MESSAGES.networkError.title, {
      message: TOAST_MESSAGES.networkError.message,
    });
  });

  it("shows readable error message on 400 plain-text response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response("Платформа не относится к произведению", {
        status: 400,
        statusText: "Bad Request",
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      }),
    );

    const result = await VorApi.quickUpdate("/library/1/quick/", "owned_platform", 99);

    expect(result).toBeNull();
    expect(errorMock).toHaveBeenCalledWith(httpStatusTitle(400), {
      message: "Платформа не относится к произведению",
      details: "",
    });
  });

  it("returns parsed JSON without auto-toast when silent option is enabled", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: false, errors: { title: [{ message: "Обязательное поле" }] } }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await VorApi.saveWork("/library/add/", new FormData());

    expect(result).toEqual({
      ok: false,
      errors: { title: [{ message: "Обязательное поле" }] },
    });
    expect(errorMock).not.toHaveBeenCalled();
  });

  it("shows server error toast with copyable details on 500 response even when silent", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response("<!DOCTYPE html><html><body>Server Error</body></html>", {
        status: 500,
        statusText: "Internal Server Error",
        headers: { "Content-Type": "text/html" },
      }),
    );

    const result = await VorApi.saveWork("/library/add/", new FormData());

    expect(result).toBeNull();
    expect(errorMock).toHaveBeenCalledTimes(1);
    const [title, opts] = errorMock.mock.calls[0];
    expect(title).toBe(httpStatusTitle(500));
    expect(opts.details).toContain("POST /library/add/ -> 500 Internal Server Error");
  });
});
