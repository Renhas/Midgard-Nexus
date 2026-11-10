export function allowedRelationTypes(relationTypes, otherType, currentType) {
  return (relationTypes || []).filter((opt) => {
    if (opt.value === "other") return true;
    if (opt.value === "adaptation") return otherType && otherType !== currentType;
    return otherType === currentType;
  });
}

export function relationKey(item) {
  return `${item.id || "new"}-${item.type_key}-${item.work_id}`;
}

export function relationLabelFor(relationTypes, type, direction) {
  const found = (relationTypes || []).find((item) => item.value === type);
  if (type === "sequel") return direction === "in" ? "Предыстория" : "Продолжение";
  if (type === "spin_off") return direction === "in" ? "Оригинал" : "Спин-офф";
  if (type === "adaptation") return direction === "in" ? "Первоисточник" : "Адаптация";
  if (type === "remake") return direction === "in" ? "Оригинал" : "Ремейк";
  return found ? found.label : "Связано";
}
