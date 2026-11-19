import { beforeEach, describe, expect, it, vi } from "vitest";

const stores = {};

vi.mock("@lib/alpine", () => ({
  getAlpine: () => ({
    store: (name) => stores[name],
  }),
}));

await import("@vor/events/list");

function pressFindShortcut(useMeta = false) {
  const event = new KeyboardEvent("keydown", {
    code: "KeyF",
    ctrlKey: !useMeta,
    metaKey: useMeta,
    cancelable: true,
  });
  document.dispatchEvent(event);
  return event;
}

describe("Library search shortcut (Ctrl+F / Cmd+F)", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="vor-artworks-opts"></div>
      <div id="vor-modal"></div>
      <div id="vor-overlay"></div>
    `;
    stores.vorArtworks = {
      openSearch: vi.fn(),
    };
  });

  it("opens search when modal and overlay are empty", () => {
    const event = pressFindShortcut();

    expect(event.defaultPrevented).toBe(true);
    expect(stores.vorArtworks.openSearch).toHaveBeenCalledTimes(1);
  });

  it("supports Cmd+F shortcut", () => {
    const event = pressFindShortcut(true);

    expect(event.defaultPrevented).toBe(true);
    expect(stores.vorArtworks.openSearch).toHaveBeenCalledTimes(1);
  });

  it("does not open search when modal is open", () => {
    document.getElementById("vor-modal").innerHTML = '<div class="vor-modal">Delete confirm</div>';

    const event = pressFindShortcut();

    expect(event.defaultPrevented).toBe(false);
    expect(stores.vorArtworks.openSearch).not.toHaveBeenCalled();
  });

  it("does not open search when overlay is open", () => {
    document.getElementById("vor-overlay").innerHTML = '<div class="vor-overlay">Details</div>';

    const event = pressFindShortcut();

    expect(event.defaultPrevented).toBe(false);
    expect(stores.vorArtworks.openSearch).not.toHaveBeenCalled();
  });

  it("ignores shortcut outside artworks page", () => {
    document.getElementById("vor-artworks-opts").remove();

    const event = pressFindShortcut();

    expect(event.defaultPrevented).toBe(false);
    expect(stores.vorArtworks.openSearch).not.toHaveBeenCalled();
  });
});
