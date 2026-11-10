import { getAlpine } from "@lib/alpine";

export function closeModal() {
  const el = document.getElementById("vor-modal");
  if (el) {
    el.innerHTML = "";
  }
}

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  if (el?.id === "vor-modal") {
    getAlpine()?.initTree?.(el);
  }
});
