"""Single Source of Truth (SSoT) domain contract for vor_archives."""

from functools import lru_cache
from typing import Any

from apps.vor_archives.artworks.forms import (
    WORK_CONDITIONAL_REQUIRED,
    WORK_FORMS,
    WORK_REQUIRED_FIELDS,
)
from apps.vor_archives.constants import (
    FilmTypeChoices,
    RELATION_LABELS,
    RELATION_SCOPES,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
    age_rating_options,
    status_options,
)
from apps.vor_archives.registry import WORK_TYPES, WORK_TYPE_REGISTRY

FIELD_TO_STATE: dict[str, dict[str, Any]] = {
    "title": {"key": "title", "trim": True},
    "film_type": {"key": "filmType"},
    "pages": {"key": "pages"},
    "duration_minutes": {"key": "durationMinutes"},
    "episode_count": {"key": "episodeCount"},
}

DRAFT_FIELD_LABELS: dict[str, str] = {
    "title": "Название",
    "description": "Описание",
    "releaseDate": "Дата релиза",
    "ageRating": "Возрастной рейтинг",
    "externalLink": "Ссылка",
    "pages": "Страницы",
    "durationMinutes": "Длительность",
    "episodeCount": "Эпизоды",
    "authors": "Авторы",
    "genres": "Жанры",
    "tags": "Теги",
    "platforms": "Платформы",
    "relations": "Связи",
}


def _build_relation_types() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for rel_type, (out_label, in_label) in RELATION_LABELS.items():
        items.append(
            {
                "value": str(rel_type),
                "label": out_label,
                "reverseLabel": in_label,
                "scope": str(RELATION_SCOPES[rel_type]),
            }
        )
    return items


def _build_work_types() -> dict[str, Any]:
    items = [
        {
            "key": meta.key,
            "label": meta.label,
            "labelPlural": meta.label_plural,
            "icon": meta.icon,
            "unit": meta.unit,
        }
        for meta in WORK_TYPE_REGISTRY.values()
    ]
    return {
        "keys": list(WORK_TYPES),
        "default": WORK_TYPES[0],
        "items": items,
    }


def _serialize_conditional_rules() -> list[dict[str, Any]]:
    serialized = []
    for rule in WORK_CONDITIONAL_REQUIRED:
        when = {
            FIELD_TO_STATE[field]["key"] if field in FIELD_TO_STATE else field: value
            for field, value in rule["when"].items()
        }
        serialized.append(
            {
                "workType": rule["workType"],
                "when": when,
                "fields": list(rule["fields"]),
            }
        )
    return serialized


def _build_validation() -> dict[str, Any]:
    return {
        "requiredByType": {
            type_key: list(fields)
            for type_key, fields in WORK_REQUIRED_FIELDS.items()
            if type_key in WORK_FORMS
        },
        "conditionalRequired": _serialize_conditional_rules(),
        "fieldToState": FIELD_TO_STATE,
        "draftLabels": DRAFT_FIELD_LABELS,
    }


@lru_cache(maxsize=1)
def get_domain_config() -> dict[str, Any]:
    """Return the complete static domain contract for vor_archives."""
    return {
        "workTypes": _build_work_types(),
        "filmTypes": {
            "default": str(FilmTypeChoices.MOVIE),
            "options": [
                {"value": str(value), "label": str(label)}
                for value, label in FilmTypeChoices.choices
            ],
        },
        "statuses": {
            "default": str(UserWorkStatusChoices.PLANNING),
            "completed": str(UserWorkStatusChoices.COMPLETED),
            "options": status_options(),
        },
        "ageRatings": {
            "options": age_rating_options(),
        },
        "relations": {
            "default": str(WorkRelationTypeChoices.OTHER),
            "types": _build_relation_types(),
        },
        "rating": {
            "min": 1,
            "max": 10,
        },
        "validation": _build_validation(),
    }
