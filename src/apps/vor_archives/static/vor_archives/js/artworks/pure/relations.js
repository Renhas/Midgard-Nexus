export function allowedRelationTypes(relationTypes, otherType, currentType) {
  return (relationTypes || []).filter((opt) => {
    const scope = opt.scope || "same";
    if (scope === "any") return true;
    if (!otherType || !currentType) return false;
    if (scope === "different") return otherType !== currentType;
    return otherType === currentType;
  });
}

export function relationKey(item) {
  return `${item.id || "new"}-${item.type_key}-${item.work_id}`;
}

export function relationLabelFor(relationTypes, type, direction) {
  const found = (relationTypes || []).find((item) => item.value === type);
  if (!found) {
    return "Связано";
  }
  if (direction === "in") {
    return found.reverseLabel || found.label || "Связано";
  }
  return found.label || "Связано";
}
