"""Registry of work type metadata and model lookups."""

from dataclasses import dataclass

from django.db.models import Model

from .models import Book, Film, Game


@dataclass(frozen=True)
class WorkTypeMeta:
    key: str
    model: type[Model]
    icon: str
    label: str
    label_plural: str
    unit: str


WORK_TYPE_REGISTRY: dict[str, WorkTypeMeta] = {
    meta.key: meta
    for meta in (
        WorkTypeMeta(
            key="book",
            model=Book,
            icon="icon-book-text",
            label="Книга",
            label_plural="Книги",
            unit="стр.",
        ),
        WorkTypeMeta(
            key="film",
            model=Film,
            icon="icon-clapperboard",
            label="Фильм",
            label_plural="Фильмы",
            unit="ч.",
        ),
        WorkTypeMeta(
            key="game",
            model=Game,
            icon="icon-gamepad-2",
            label="Игра",
            label_plural="Игры",
            unit="ч.",
        ),
    )
}


WORK_TYPES: tuple[str, ...] = tuple(WORK_TYPE_REGISTRY)

WORK_MODELS: dict[str, type[Model]] = {
    key: meta.model for key, meta in WORK_TYPE_REGISTRY.items()
}

WORK_TYPE_ICONS: dict[str, str] = {
    key: meta.icon for key, meta in WORK_TYPE_REGISTRY.items()
}

WORK_TYPE_LABELS: dict[str, str] = {
    key: meta.label for key, meta in WORK_TYPE_REGISTRY.items()
}

WORK_TYPE_LABELS_PLURAL: dict[str, str] = {
    key: meta.label_plural for key, meta in WORK_TYPE_REGISTRY.items()
}

WORK_TYPE_UNITS: dict[str, str] = {
    key: meta.unit for key, meta in WORK_TYPE_REGISTRY.items()
}


def get_work_model(type_key: str) -> type[Model]:
    try:
        return WORK_MODELS[type_key]
    except KeyError:
        raise ValueError(f"Unknown work type: {type_key}")
