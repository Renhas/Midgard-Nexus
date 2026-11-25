import { getDomainConfig } from "@vor/shared/domain";

export function getStatusMixin({ status, choices } = {}) {
  const statusesConfig = getDomainConfig().statuses || {};
  const defaultStatus = statusesConfig.default || "planning";
  const resolvedStatus = status ?? defaultStatus;
  const resolvedChoices = choices ?? statusesConfig.options ?? [];

  return {
    status: resolvedStatus,
    statusChoices: resolvedChoices,
    statusOpen: false,
    statusLabel() {
      const found = this.statusChoices.find((item) => item.value === this.status);
      return found ? found.label : this.status || defaultStatus;
    },
    setStatus(value) {
      this.statusOpen = false;
      if (this.status === value) return;
      this.status = value;
      if (typeof this.saveField === "function") {
        this.saveField("status", value);
      }
    },
  };
}
