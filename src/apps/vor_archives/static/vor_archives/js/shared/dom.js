export function hasContent(id) {
  const el = document.getElementById(id);
  return Boolean(el && el.innerHTML.trim());
}
