from apps.vor_archives.constants import WorkRelationTypeChoices

RELATION_TYPE_OPTIONS = [
    {"value": WorkRelationTypeChoices.SEQUEL, "label": "Продолжение"},
    {"value": WorkRelationTypeChoices.SPIN_OFF, "label": "Спин-офф"},
    {"value": WorkRelationTypeChoices.ADAPTATION, "label": "Адаптация"},
    {"value": WorkRelationTypeChoices.REMAKE, "label": "Ремейк"},
    {"value": WorkRelationTypeChoices.OTHER, "label": "Связано"},
]
