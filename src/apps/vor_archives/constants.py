from typing import NamedTuple

from django.db import models

# TODO: Remove duplicates in UserWork & FeedItemAction Types
# TODO: Localization (RU) for types


class AgeRatingChoices(models.TextChoices):
    RATING_0 = ("0+", "0+")
    RATING_6 = ("6+", "6+")
    RATING_12 = ("12+", "12+")
    RATING_16 = ("16+", "16+")
    RATING_18 = ("18+", "18+")


class FilmTypeChoices(models.TextChoices):
    MOVIE = ("movie", "Movie")
    TV_SHOW = ("tv_show", "TV Show")


class WorkRelationTypeChoices(models.TextChoices):
    SEQUEL = ("sequel", "Sequel")
    SPIN_OFF = ("spin_off", "Spin-off")
    ADAPTATION = ("adaptation", "Adaptation")
    REMAKE = ("remake", "Remake")
    OTHER = ("other", "Other")


class UserWorkStatusChoices(models.TextChoices):
    PLANNING = ("planning", "Planning")
    IN_PROGRESS = ("in_progress", "In Progress")
    COMPLETED = ("completed", "Completed")
    DROPPED = ("dropped", "Dropped")


class FeedItemActionTypeChoices(models.TextChoices):
    ADDED = ("added", "Added")
    PLANNING = ("planning", "Planning")
    IN_PROGRESS = ("in_progress", "In Progress")
    COMPLETED = ("completed", "Completed")
    DROPPED = ("dropped", "Dropped")
    RATED = ("rated", "Rated")


class FeedActionMeta(NamedTuple):
    label: str
    icon: str


FEED_ACTION_META: dict[str, FeedActionMeta] = {
    "added": FeedActionMeta("Добавлено", "bi bi-plus-circle"),
    "planning": FeedActionMeta("Запланировано", "bi bi-clock"),
    "in_progress": FeedActionMeta("В процессе", "bi bi-play-circle"),
    "completed": FeedActionMeta("Завершено", "bi bi-check-circle"),
    "dropped": FeedActionMeta("Брошено", "bi bi-x-circle"),
    "rated": FeedActionMeta("Оценка", "bi bi-star"),
}

FEED_ACTION_LABELS_RU: dict[str, str] = {
    key: meta.label for key, meta in FEED_ACTION_META.items()
}

FEED_ACTION_ICONS: dict[str, str] = {
    key: meta.icon for key, meta in FEED_ACTION_META.items()
}

STATUS_LABELS_RU = {
    UserWorkStatusChoices.PLANNING: "Запланировано",
    UserWorkStatusChoices.IN_PROGRESS: "В процессе",
    UserWorkStatusChoices.COMPLETED: "Завершено",
    UserWorkStatusChoices.DROPPED: "Брошено",
}

STATUS_SORT_ORDER = {
    UserWorkStatusChoices.PLANNING: 0,
    UserWorkStatusChoices.IN_PROGRESS: 1,
    UserWorkStatusChoices.COMPLETED: 2,
    UserWorkStatusChoices.DROPPED: 3,
}

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
