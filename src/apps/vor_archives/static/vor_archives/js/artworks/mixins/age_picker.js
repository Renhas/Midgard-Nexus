import { wheelDirection } from "@vor/shared/pure/wheel";

export function getAgePickerMixin({
  ageChoices = [],
} = {}) {
  return {
    ageOpen: false,
    ageChoices,
    setAgeRating(value) {
      this.ageRating = value;
      this.ageOpen = false;
    },
    ageLabel() {
      const found = this.ageChoices.find((item) => item.value === this.ageRating);
      return found ? found.label : "Возрастной рейтинг";
    },
    onAgeWheel(event) {
      const direction = wheelDirection(event.deltaY);
      if (!direction) {
        return;
      }
      const options = [""].concat((this.ageChoices || []).map((item) => item.value));
      const index = Math.max(0, options.indexOf(this.ageRating || ""));
      const next = Math.max(0, Math.min(options.length - 1, index + direction));
      this.ageRating = options[next];
    },
  };
}
