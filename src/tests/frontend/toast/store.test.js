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

  it("adds toasts, dismisses on progress animation end, and removes after exit animation", () => {
    const store = createToastStore(TEST_CONFIG);
    const id = store.show({ level: "success", message: "Готово", duration: 2000 });

    expect(id).toBe(1);
    expect(store.items).toHaveLength(1);

    store.onProgressEnd(id);
    expect(store.items[0].closing).toBe(true);

    vi.advanceTimersByTime(250);
    expect(store.items).toHaveLength(0);
  });

  it("evicts oldest active toast when maxVisible limit is exceeded", () => {
    const store = createToastStore(TEST_CONFIG);
    store.show({ message: "1" });
    store.show({ message: "2" });
    store.show({ message: "3" });
    store.show({ message: "4" });

    expect(store.items[0].closing).toBe(true);
    vi.advanceTimersByTime(250);
    expect(store.items.map((item) => item.message)).toEqual(["2", "3", "4"]);
  });

  it("keeps expanded state briefly on leave and cancels collapse on re-enter", () => {
    const store = createToastStore(TEST_CONFIG);
    const firstId = store.show({ message: "Первый", duration: 0 });
    store.show({ message: "Второй", duration: 0 });

    store.expand();
    expect(store.expanded).toBe(true);

    store.dismiss(firstId);
    vi.advanceTimersByTime(250);
    expect(store.items).toHaveLength(1);
    expect(store.expanded).toBe(true);

    store.scheduleCollapse();
    expect(store.expanded).toBe(true);

    store.expand();
    vi.advanceTimersByTime(250);
    expect(store.expanded).toBe(true);

    store.scheduleCollapse();
    vi.advanceTimersByTime(200);
    expect(store.expanded).toBe(false);
  });

  it("dismisses all toasts at once and resets expanded state", () => {
    const store = createToastStore(TEST_CONFIG);
    store.show({ message: "Первый", duration: 0 });
    store.show({ message: "Второй", duration: 0 });
    store.expand();

    expect(store.hasMultiple).toBe(true);
    store.dismissAll();

    vi.advanceTimersByTime(250);
    expect(store.items).toHaveLength(0);
    expect(store.expanded).toBe(false);
  });

  it("dispatches custom event or runs callback on action trigger and dismisses toast", () => {
    const store = createToastStore(TEST_CONFIG);
    const onClick = vi.fn();
    const eventSpy = vi.fn();
    document.body.addEventListener("test:toast-action", eventSpy);

    store.show({
      message: "Первое",
      duration: 0,
      action: { label: "Клик", onClick },
    });
    store.show({
      message: "Второе",
      duration: 0,
      action: { label: "Событие", event: "test:toast-action", detail: { id: 7 } },
    });

    store.triggerAction(store.items[0]);
    expect(onClick).toHaveBeenCalledTimes(1);

    store.triggerAction(store.items[1]);
    expect(eventSpy).toHaveBeenCalledTimes(1);
    expect(eventSpy.mock.calls[0][0].detail).toEqual({ id: 7 });

    vi.advanceTimersByTime(250);
    expect(store.items).toHaveLength(0);
    document.body.removeEventListener("test:toast-action", eventSpy);
  });
});
