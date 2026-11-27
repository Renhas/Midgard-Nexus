import { getAlpine } from "@lib/alpine";

function store() {
  return getAlpine()?.store("toasts") || null;
}

export const notify = {
  show(payload) {
    return store()?.show(payload) ?? null;
  },
  success(title, options = {}) {
    return this.show({ ...options, level: "success", title });
  },
  error(title, options = {}) {
    return this.show({ ...options, level: "error", title });
  },
  info(title, options = {}) {
    return this.show({ ...options, level: "info", title });
  },
  dismiss(id) {
    store()?.dismiss(id);
  },
  dismissAll() {
    store()?.dismissAll();
  },
};

export default notify;
