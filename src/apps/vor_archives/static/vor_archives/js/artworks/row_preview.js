import { getAlpine } from "@lib/alpine";
import { FloatingUI } from "@lib/floating-ui";

const OFFSET = 14;
const PAD = 12;
const SHOW_DELAY = 180;
let preview = null;
let currentItem = null;
let showTimer = 0;
let placeSeq = 0;
let lastX = 0;
let lastY = 0;

function ensurePreview() {
  if (preview) {
    return preview;
  }
  preview = document.createElement("div");
  preview.id = "vor-artwork-row-preview";
  preview.className = "vor-panel vor-artwork-row-preview";
  preview.innerHTML = `
            <div class="vor-artwork-row-preview-cover">
                <img alt="">
                <div class="vor-artwork-row-preview-cover-empty"><i></i></div>
            </div>
            <div class="vor-artwork-row-preview-body">
                <div class="vor-artwork-row-preview-title"></div>
                <div class="vor-artwork-row-preview-desc"></div>
            </div>
        `;
  document.body.appendChild(preview);
  return preview;
}

function hidePreview() {
  window.clearTimeout(showTimer);
  showTimer = 0;
  currentItem = null;
  placeSeq += 1;
  if (preview) {
    preview.classList.remove("vor-artwork-row-preview--visible");
    preview.style.visibility = "";
  }
}

function canShow(row) {
  if (!row) {
    return false;
  }
  if (document.body.dataset.dragging) {
    return false;
  }
  const list = row.closest(".vor-artwork-list");
  if (!list || list.classList.contains("is-grid")) {
    return false;
  }
  if (getAlpine()?.store("vorArtworks")?.searchOpen) {
    return false;
  }
  if (getAlpine()?.store("vorArtworks")?.menu?.open) {
    return false;
  }
  return true;
}

function fillPreview(item) {
  const el = ensurePreview();
  const title = item.dataset.previewTitle || "";
  const cover = item.dataset.previewCover || "";
  el.querySelector(".vor-artwork-row-preview-title").textContent = title;
  el.querySelector(".vor-artwork-row-preview-desc").textContent = (item.dataset.previewDesc || "")
    .replace(/\s+/g, " ")
    .trim();
  const img = el.querySelector("img");
  img.alt = title;
  if (cover) {
    img.src = cover;
    el.classList.remove("vor-artwork-row-preview--empty");
  } else {
    img.removeAttribute("src");
    el.classList.add("vor-artwork-row-preview--empty");
    const icon = el.querySelector(".vor-artwork-row-preview-cover-empty i");
    if (icon) {
      icon.className = item.dataset.previewIcon || "";
    }
  }
}

function getSafeBoundary() {
  const sidebar = document.querySelector(".sidebar--right");
  if (!sidebar || sidebar.classList.contains("sidebar--collapsed")) {
    return { x: 0, y: 0, width: window.innerWidth, height: window.innerHeight };
  }
  const rect = sidebar.getBoundingClientRect();
  return { x: 0, y: 0, width: rect.left, height: window.innerHeight };
}

async function placePreview() {
  const el = ensurePreview();
  const seq = (placeSeq += 1);
  const x = lastX;
  const y = lastY;
  el.classList.add("vor-artwork-row-preview--visible");
  el.style.visibility = "hidden";
  const virtualEl = {
    getBoundingClientRect: () => ({
      x,
      y,
      top: y,
      left: x,
      right: x,
      bottom: y,
      width: 0,
      height: 0,
    }),
  };
  const boundary = getSafeBoundary();
  let coords;
  try {
    coords = await FloatingUI.computePosition(virtualEl, el, {
      placement: "right-start",
      strategy: "fixed",
      middleware: [
        // Offset is asymmetric. A right placement starts OFFSET
        // past the cursor so the tooltip does not visually touch the
        // pointer that triggered it. A left placement should sit flush
        // against the cursor (0), because the tooltip grows leftward from
        // the pointer and any gap reads as "not attached". Read placement
        // inside the callback: flip may switch sides between calls.
        FloatingUI.offset(({ placement }) => ({
          mainAxis: placement.startsWith("left") ? 0 : OFFSET,
        })),
        FloatingUI.flip({ boundary, padding: PAD }),
        FloatingUI.shift({ boundary, padding: PAD }),
      ],
    });
  } catch {
    if (seq === placeSeq) {
      hidePreview();
    }
    return;
  }
  if (seq !== placeSeq) {
    return;
  }
  el.style.left = `${coords.x}px`;
  el.style.top = `${coords.y}px`;
  el.style.visibility = "";
}

document.addEventListener("pointermove", (event) => {
  lastX = event.clientX;
  lastY = event.clientY;
  const row = event.target.closest(".vor-artwork-row");
  const item = row?.closest(".vor-artwork-item");
  if (!canShow(row) || !item) {
    hidePreview();
    return;
  }
  if (currentItem !== item) {
    currentItem = item;
    fillPreview(item);
    window.clearTimeout(showTimer);
    if (preview?.classList.contains("vor-artwork-row-preview--visible")) {
      void placePreview();
      return;
    }
    // Do not capture the event: by the time the timer fires the cursor
    // may have moved on. placePreview reads lastX/lastY at call time.
    showTimer = window.setTimeout(() => {
      if (currentItem === item) {
        void placePreview();
      }
    }, SHOW_DELAY);
    return;
  }
  if (preview?.classList.contains("vor-artwork-row-preview--visible")) {
    void placePreview();
  }
});

document.addEventListener("pointerdown", hidePreview);
window.addEventListener("blur", hidePreview);
window.addEventListener("scroll", hidePreview, true);
