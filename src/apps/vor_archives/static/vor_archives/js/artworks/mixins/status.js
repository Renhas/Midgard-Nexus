import { getDomainConfig } from "@vor/shared/domain";

export function getStatusMixin({ status } = {}) {
  const { default: defaultStatus, options } = getDomainConfig().statuses;

  return {
    status: status ?? defaultStatus,
    statusChoices: options,
    statusOpen: false,
    statusLabel() {
      const found = this.statusChoices.find((item) => item.value === this.status);
      return found ? found.label : this.status;
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
