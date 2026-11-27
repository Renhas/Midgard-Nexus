import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createToastStore } from "@toast/store";

const TEST_CONFIG = {
  maxVisible: 3,
  duration: 4000,
  errorDuration: 7000,
};

describe("Toast store lifecycle", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("ignores toast payloads without a title", () => {
    const store = createToastStore(TEST_CONFIG);
    expect(store.show({ message: "Без заголовка" })).toBeNull();
    expect(store.items).toHaveLength(0);
  });

  it("adds toasts, dismisses on progress animation end, and removes after exit animation", () => {
    const store = createToastStore(TEST_CONFIG);
    const id = store.show({ level: "success", title: "Готово", duration: 2000 });

    expect(id).toBe(1);
    expect(store.items).toHaveLength(1);

    store.onProgressEnd(id);
    expect(store.isClosing(id)).toBe(true);

    vi.advanceTimersByTime(300);
    expect(store.items).toHaveLength(0);
  });

  it("keeps overflow toasts queued and reveals older ones when newer are dismissed", () => {
    const store = createToastStore(TEST_CONFIG);
    store.show({ title: "1", duration: 0 });
    store.show({ title: "2", duration: 0 });
    const thirdId = store.show({ title: "3", duration: 0 });
    store.show({ title: "4", duration: 0 });

    expect(store.visibleItems.map((item) => item.title)).toEqual(["2", "3", "4"]);

    store.dismiss(thirdId);
    vi.advanceTimersByTime(300);
    expect(store.visibleItems.map((item) => item.title)).toEqual(["1", "2", "4"]);
  });

  it("keeps expanded state when dismissing an item until pointer leaves", () => {
    const store = createToastStore(TEST_CONFIG);
    const firstId = store.show({ title: "Первый", duration: 0 });
    store.show({ title: "Второй", duration: 0 });

    store.expand();
    expect(store.expanded).toBe(true);

    store.dismiss(firstId);
    vi.advanceTimersByTime(300);
    expect(store.items).toHaveLength(1);
    expect(store.expanded).toBe(true);

    store.collapse();
    expect(store.expanded).toBe(false);
  });

  it("dismisses all toasts at once and resets expanded state", () => {
    const store = createToastStore(TEST_CONFIG);
    store.show({ title: "Первый", duration: 0 });
    store.show({ title: "Второй", duration: 0 });
    store.expand();

    expect(store.hasMultiple).toBe(true);
    store.dismissAll();

    vi.advanceTimersByTime(400);
    expect(store.items).toHaveLength(0);
    expect(store.expanded).toBe(false);
  });

  it("dispatches custom event or runs callback on action trigger and dismisses toast", () => {
    const store = createToastStore(TEST_CONFIG);
    const onClick = vi.fn();
    const eventSpy = vi.fn();
    document.body.addEventListener("test:toast-action", eventSpy);

    store.show({
      title: "Первое",
      duration: 0,
      action: { label: "Клик", onClick },
    });
    store.show({
      title: "Второе",
      duration: 0,
      action: { label: "Событие", event: "test:toast-action", detail: { id: 7 } },
    });

    store.triggerAction(store.items[0]);
    expect(onClick).toHaveBeenCalledTimes(1);

    store.triggerAction(store.items[1]);
    expect(eventSpy).toHaveBeenCalledTimes(1);
    expect(eventSpy.mock.calls[0][0].detail).toEqual({ id: 7 });

    vi.advanceTimersByTime(300);
    expect(store.items).toHaveLength(0);
    document.body.removeEventListener("test:toast-action", eventSpy);
  });
});
