import {
  filterCatalogue,
  isSelected,
  toggleSelection,
  addSelection,
  removeSelection,
} from "@vor/artworks/pure/catalogs";

export function getAttributeMixin({ catalogs = {} } = {}) {
  return {
    catalogs,
    pickerKind: null,
    pickerQuery: "",
    attributeCatalogue(kind) {
      const byType = this.catalogs[this.workType] || {};
      return byType[kind] || [];
    },
    filterCatalog(kind, query) {
      return filterCatalogue(this.attributeCatalogue(kind), query);
    },
    hasAttr(kind, id) {
      return isSelected(this[kind], id);
    },
    toggleAttr(kind, opt) {
      this[kind] = toggleSelection(this[kind], opt);
    },
    pickerOptions(kind) {
      const query = String(this.pickerQuery || "").trim();
      return filterCatalogue(this.attributeCatalogue(kind), query)
        .filter((item) => !isSelected(this[kind], item.id));
    },
    addPickerItem(kind, opt) {
      this[kind] = addSelection(this[kind], opt);
    },
    removeChip(kind, id) {
      this[kind] = removeSelection(this[kind], id);
    },
    togglePicker(kind) {
      if (this.pickerKind === kind) {
        this.closePicker();
        return;
      }
      this.pickerKind = kind;
      this.pickerQuery = "";
    },
    closePicker() {
      this.pickerKind = null;
      this.pickerQuery = "";
    },
  };
}
