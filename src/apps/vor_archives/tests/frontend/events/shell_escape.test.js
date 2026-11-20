import { beforeEach, describe, expect, it, vi } from "vitest";

const stores = {};

vi.mock("@lib/alpine", () => ({
  getAlpine: () => ({
    store: (name) => stores[name],
    $data: () => null,
  }),
}));

await import("@vor/events/shell");
await import("@vor/events/attributes");

function pressEscape() {
  const event = new KeyboardEvent("keydown", { key: "Escape", cancelable: true });
  document.dispatchEvent(event);
  return event;
}

describe("Escape key priority in shell and attributes", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="vor-modal"></div>
      <div id="vor-overlay"></div>
    `;
    stores.vorArtworks = {
      menu: { open: false },
      searchOpen: false,
      deleteMode: false,
      closeMenu: vi.fn(function () {
        this.menu.open = false;
      }),
      closeSearch: vi.fn(function () {
        this.searchOpen = false;
      }),
      exitDeleteMode: vi.fn(function () {
        this.deleteMode = false;
      }),
    };
    stores.vorAttributes = {
      deleteMode: false,
      selectedIds: [],
      exitDeleteMode: vi.fn(function () {
        this.deleteMode = false;
        this.selectedIds = [];
      }),
    };
  });

  it("closes modal on Escape without exiting attributes delete mode", () => {
    document.body.insertAdjacentHTML("beforeend", '<div class="vor-attr-page"></div>');
    document.getElementById("vor-modal").innerHTML = '<div class="vor-modal">Confirm</div>';
    stores.vorAttributes.deleteMode = true;
    stores.vorAttributes.selectedIds = ["1", "2"];

    pressEscape();

    expect(document.getElementById("vor-modal").innerHTML).toBe("");
    expect(stores.vorAttributes.exitDeleteMode).not.toHaveBeenCalled();
    expect(stores.vorAttributes.deleteMode).toBe(true);
    expect(stores.vorAttributes.selectedIds).toEqual(["1", "2"]);
  });

  it("exits attributes delete mode on Escape when modal is empty", () => {
    document.body.insertAdjacentHTML("beforeend", '<div class="vor-attr-page"></div>');
    stores.vorAttributes.deleteMode = true;
    stores.vorAttributes.selectedIds = ["1"];

    pressEscape();

    expect(stores.vorAttributes.exitDeleteMode).toHaveBeenCalledTimes(1);
    expect(stores.vorAttributes.deleteMode).toBe(false);
    expect(stores.vorAttributes.selectedIds).toEqual([]);
  });

  it("follows strict priority cascade on artworks page", () => {
    document.getElementById("vor-modal").innerHTML = "<div>Modal</div>";
    document.getElementById("vor-overlay").innerHTML = "<div>Overlay</div>";
    stores.vorArtworks.menu.open = true;
    stores.vorArtworks.searchOpen = true;
    stores.vorArtworks.deleteMode = true;

    pressEscape();
    expect(stores.vorArtworks.closeMenu).toHaveBeenCalledTimes(1);
    expect(stores.vorArtworks.searchOpen).toBe(true);

    pressEscape();
    expect(stores.vorArtworks.closeSearch).toHaveBeenCalledTimes(1);
    expect(document.getElementById("vor-modal").innerHTML).not.toBe("");

    pressEscape();
    expect(document.getElementById("vor-modal").innerHTML).toBe("");
    expect(document.getElementById("vor-overlay").innerHTML).not.toBe("");

    pressEscape();
    expect(document.getElementById("vor-overlay").innerHTML).toBe("");
    expect(stores.vorArtworks.deleteMode).toBe(true);

    pressEscape();
    expect(stores.vorArtworks.exitDeleteMode).toHaveBeenCalledTimes(1);
    expect(stores.vorArtworks.deleteMode).toBe(false);
  });
});
