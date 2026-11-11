import {
  DATE_MONTHS_FULL,
  DATE_MONTHS_SHORT,
  toIsoDate,
  buildDateCells,
  yearGridStart,
  buildYearCells,
} from "@vor/artworks/pure/dates";

export function getDatePickerMixin({ dateCursor = null } = {}) {
  return {
    dateOpen: false,
    dateCursor,
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
  };
}
