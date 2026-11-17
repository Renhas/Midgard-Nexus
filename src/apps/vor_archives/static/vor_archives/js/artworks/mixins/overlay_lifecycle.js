import { closeOverlay as closeOverlayImpl } from "@vor/shared/overlay_lifecycle";

export function getOverlayLifecycleMixin() {
  return {
    closeOverlay() {
      return closeOverlayImpl();
    },
    refreshList() {
      document.body.dispatchEvent(new CustomEvent("vor:reload-list"));
    },
  };
}
