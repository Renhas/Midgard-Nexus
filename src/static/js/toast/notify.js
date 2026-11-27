import { getAlpine } from "@lib/alpine";

function store() {
  return getAlpine()?.store("toasts") || null;
}

export const notify = {
  show(payload) {
    return store()?.show(payload) ?? null;
  },
  success(message, options = {}) {
    return this.show({ ...options, level: "success", message });
  },
  error(message, options = {}) {
    return this.show({ ...options, level: "error", message });
  },
  info(message, options = {}) {
    return this.show({ ...options, level: "info", message });
  },
  dismiss(id) {
    store()?.dismiss(id);
  },
  dismissAll() {
    store()?.dismissAll();
  },
};

export default notify;
