export function toggleSelectedId(selectedIds, id) {
  const target = String(id);
  if (!target) {
    return [...selectedIds];
  }
  return selectedIds.includes(target) ? selectedIds.filter((item) => item !== target) : [...selectedIds, target];
}

export function hasSelectedId(selectedIds, id) {
  return selectedIds.includes(String(id));
}

export function buildDeletePreviewUrl(baseUrl, selectedIds) {
  if (!baseUrl || !selectedIds.length) {
    return "";
  }
  const params = selectedIds.map((id) => `ids=${encodeURIComponent(id)}`).join("&");
  return `${baseUrl}?${params}`;
}
