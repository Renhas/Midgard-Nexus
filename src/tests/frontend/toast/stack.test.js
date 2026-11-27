import { describe, expect, it } from "vitest";
import {
  computeStackSlots,
  createToastEntry,
  extractErrorMessage,
  normalizeToastConfig,
  normalizeToastLevel,
  readToastConfig,
  resolveToastDuration,
} from "@toast/stack";

const TEST_CONFIG = {
  maxVisible: 5,
  duration: 4000,
  errorDuration: 7000,
};

describe("Toast stack pure helpers", () => {
  it("reads and validates config from JSON script tag", () => {
    document.body.innerHTML = `<script id="app-toast-config" type="application/json">{"maxVisible":3,"duration":2500,"errorDuration":6000}</script>`;
    expect(readToastConfig()).toEqual({
      maxVisible: 3,
      duration: 2500,
      errorDuration: 6000,
    });

    expect(() => normalizeToastConfig({ maxVisible: 0, duration: 1000, errorDuration: 2000 })).toThrow();
    expect(() => normalizeToastConfig({ maxVisible: 3, duration: -1, errorDuration: 2000 })).toThrow();
  });

  it("normalizes unknown toast levels to info", () => {
    expect(normalizeToastLevel("success")).toBe("success");
    expect(normalizeToastLevel("ERROR")).toBe("error");
    expect(normalizeToastLevel("warning")).toBe("info");
    expect(normalizeToastLevel("")).toBe("info");
  });

  it("resolves durations based on level and explicit overrides", () => {
    expect(resolveToastDuration("success", undefined, TEST_CONFIG)).toBe(4000);
    expect(resolveToastDuration("error", undefined, TEST_CONFIG)).toBe(7000);
    expect(resolveToastDuration("error", 0, TEST_CONFIG)).toBe(0);
    expect(resolveToastDuration("info", 1500, TEST_CONFIG)).toBe(1500);
  });

  it("creates normalized toast entries from string or object", () => {
    const simple = createToastEntry("Сохранено", 1, TEST_CONFIG);
    expect(simple).toMatchObject({
      id: 1,
      level: "info",
      message: "Сохранено",
      details: "",
      duration: 4000,
      action: null,
      copied: false,
      closing: false,
    });

    const rich = createToastEntry(
      {
        level: "error",
        message: "  Ошибка  ",
        details: "Traceback...",
        action: { label: "Открыть", event: "vor:open", detail: { id: 42 } },
      },
      2,
      TEST_CONFIG,
    );
    expect(rich.message).toBe("Ошибка");
    expect(rich.details).toBe("Traceback...");
    expect(rich.action).toEqual({
      label: "Открыть",
      onClick: null,
      event: "vor:open",
      detail: { id: 42 },
    });
  });

  it("computes stack indices from newest to oldest", () => {
    const slots = computeStackSlots([{ id: 1 }, { id: 2 }, { id: 3 }]);
    expect(slots).toEqual([
      { id: 1, stackIndex: 2 },
      { id: 2, stackIndex: 1 },
      { id: 3, stackIndex: 0 },
    ]);
  });

  it("extracts readable messages from JSON or plain text and falls back on HTML", () => {
    expect(extractErrorMessage('{"error":"Коллекция уже существует"}', "application/json")).toBe(
      "Коллекция уже существует",
    );
    expect(extractErrorMessage('{"message":"Неверный формат"}', "application/json")).toBe("Неверный формат");
    expect(extractErrorMessage('{"errors":{"__all__":[{"message":"Ошибка связи"}]}}', "application/json")).toBe(
      "Ошибка связи",
    );
    expect(extractErrorMessage("Недостаточно прав", "text/plain; charset=utf-8")).toBe("Недостаточно прав");
    expect(extractErrorMessage("<!DOCTYPE html><html><body>500</body></html>", "text/html", "Ошибка сервера")).toBe(
      "Ошибка сервера",
    );
    expect(extractErrorMessage("", "text/plain", "Сбой")).toBe("Сбой");
  });
});
