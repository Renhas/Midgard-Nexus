export function mergeFilterSelection(allIds, savedSelected, savedKnown) {
  const catalog = allIds || [];
  if (!savedSelected && !savedKnown) {
    return [...catalog];
  }
  const selected = new Set((savedSelected || []).map(String));
  const known = new Set((savedKnown || []).map(String));
  return catalog.filter((id) => {
    const key = String(id);
    return !known.has(key) || selected.has(key);
  });
}
