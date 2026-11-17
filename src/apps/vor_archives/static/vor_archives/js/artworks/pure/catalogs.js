export function filterCatalogue(items, query) {
  const q = String(query || "")
    .trim()
    .toLowerCase();
  return (items || []).filter(
    (item) =>
      !q ||
      String(item.name || "")
        .toLowerCase()
        .includes(q),
  );
}

export function isSelected(list, id) {
  return (list || []).some((item) => Number(item.id) === Number(id));
}

export function toggleSelection(list, item) {
  if (isSelected(list, item.id)) {
    return (list || []).filter((entry) => Number(entry.id) !== Number(item.id));
  }
  return [...(list || []), item];
}

export function addSelection(list, item) {
  if (isSelected(list, item.id)) {
    return list;
  }
  return [...(list || []), item];
}

export function removeSelection(list, id) {
  return (list || []).filter((item) => Number(item.id) !== Number(id));
}
