export function getStatusMixin({
  status = "planning",
  choices = [],
} = {}) {
  return {
    status,
    statusChoices: choices,
    statusOpen: false,
    statusLabel() {
      const found = this.statusChoices.find((item) => item.value === this.status);
      return found ? found.label : (this.status || "planning");
    },
    setStatus(value) {
      this.statusOpen = false;
      if (this.status === value) return;
      this.status = value;
      if (value === "completed" && this.progressMax != null) {
        this.progress = this.progressMax;
      }
      if (value === "in_progress") {
        this.progress = 0;
      }
      if (typeof this.saveField === "function") {
        this.saveField("status", value);
      }
    }
  };
}
