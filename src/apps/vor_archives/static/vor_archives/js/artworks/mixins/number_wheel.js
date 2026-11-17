import { wheelDirection } from "@vor/shared/pure/wheel";

export function getNumberWheelMixin() {
  return {
    onNumberWheel(event, field, min = 1, max = null) {
      const direction = wheelDirection(event.deltaY);
      if (!direction) {
        return;
      }
      const raw = this[field];
      const value = raw === "" || raw == null ? 0 : Number(raw);
      const current = Number.isFinite(value) ? value : 0;
      let next = current + direction;
      if (next < min) {
        next = current === 0 && direction < 0 ? 0 : min;
      }
      if (max != null && next > max) {
        next = max;
      }
      this[field] = next < min ? "" : next;
    },
  };
}
