from apps.vor_archives.constants import WorkRelationTypeChoices


RELATION_LABELS = {
    WorkRelationTypeChoices.SEQUEL: ("Продолжение", "Предыстория"),
    WorkRelationTypeChoices.SPIN_OFF: ("Спин-офф", "Оригинал"),
    WorkRelationTypeChoices.ADAPTATION: ("Адаптация", "Первоисточник"),
    WorkRelationTypeChoices.REMAKE: ("Ремейк", "Оригинал"),
    WorkRelationTypeChoices.OTHER: ("Связано", "Связано"),
}


RELATION_TYPE_OPTIONS = [
    {"value": rel_type, "label": labels[0]}
    for rel_type, labels in RELATION_LABELS.items()
]
