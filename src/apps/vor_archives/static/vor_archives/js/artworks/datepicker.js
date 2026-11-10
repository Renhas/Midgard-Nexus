import {
  DATE_MONTHS_FULL,
  DATE_MONTHS_SHORT,
  toIsoDate,
  buildDateCells,
  yearGridStart,
  buildYearCells,
} from "@vor/artworks/pure/dates";
import { wheelDirection } from "@vor/shared/pure/wheel";

export function datePickerApi() {
  return {
    dateView: "days",
    formatDate(iso) {
      if (!iso) {
        return "";
      }
      const [year, month, day] = iso.split("-");
      return `${day}.${month}.${year}`;
    },
    dateCursorDate() {
      return this.dateCursor || new Date();
    },
    dateMonthLabel() {
      const cursor = this.dateCursorDate();
      return `${DATE_MONTHS_FULL[cursor.getMonth()]} ${cursor.getFullYear()}`;
    },
    dateHeaderLabel() {
      if (this.dateView === "years") {
        const start = yearGridStart(this.dateCursorDate().getFullYear());
        return `${start}–${start + 11}`;
      }
      if (this.dateView === "months") {
        return String(this.dateCursorDate().getFullYear());
      }
      return this.dateMonthLabel();
    },
    toggleDateOpen() {
      this.dateOpen = !this.dateOpen;
      if (this.dateOpen) {
        this.dateView = "days";
      }
    },
    closeDatePopup() {
      this.dateOpen = false;
      this.dateView = "days";
    },
    onDateHeaderClick() {
      if (this.dateView === "days") {
        this.dateView = "months";
        return;
      }
      if (this.dateView === "months") {
        this.dateView = "years";
      }
    },
    shiftDateNav(delta) {
      const cursor = new Date(this.dateCursorDate());
      if (this.dateView === "years") {
        cursor.setFullYear(cursor.getFullYear() + delta * 12);
      } else if (this.dateView === "months") {
        cursor.setFullYear(cursor.getFullYear() + delta);
      } else {
        cursor.setMonth(cursor.getMonth() + delta);
      }
      this.dateCursor = cursor;
    },
    shiftMonth(delta) {
      this.shiftDateNav(delta);
    },
    dateCells() {
      return buildDateCells(this.dateCursorDate());
    },
    monthCells() {
      return DATE_MONTHS_SHORT;
    },
    yearGridStart() {
      return yearGridStart(this.dateCursorDate().getFullYear());
    },
    yearCells() {
      return buildYearCells(this.yearGridStart());
    },
    isMonthSelected(index) {
      return this.dateCursorDate().getMonth() === index;
    },
    isYearSelected(year) {
      return this.dateCursorDate().getFullYear() === year;
    },
    selectMonth(index) {
      const cursor = new Date(this.dateCursorDate());
      cursor.setMonth(index);
      this.dateCursor = cursor;
      this.dateView = "days";
    },
    selectYear(year) {
      const cursor = new Date(this.dateCursorDate());
      cursor.setFullYear(year);
      this.dateCursor = cursor;
      this.dateView = "months";
    },
    setReleaseDate(iso) {
      this.releaseDate = iso;
      this.dateOpen = false;
      this.dateView = "days";
      if (iso) {
        this.dateCursor = new Date(`${iso}T00:00:00`);
      }
    },
    setTodayDate() {
      this.setReleaseDate(toIsoDate(new Date()));
    },
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
    onFilmTypeWheel(event) {
      const direction = wheelDirection(event.deltaY);
      if (!direction) {
        return;
      }
      const options = ["movie", "tv_show"];
      const index = Math.max(0, options.indexOf(this.filmType || "movie"));
      const next = Math.max(0, Math.min(options.length - 1, index + direction));
      this.filmType = options[next];
    },
  };
}
