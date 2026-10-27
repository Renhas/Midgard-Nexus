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


WORK_TYPES = ("book", "film", "game")

WORK_TYPE_ICONS = {
    "book": "icon-book-text",
    "film": "icon-clapperboard",
    "game": "icon-gamepad-2",
}

WORK_TYPE_LABELS = {
    "book": "Книга",
    "film": "Фильм",
    "game": "Игра",
}

WORK_TYPE_LABELS_PLURAL = {
    "book": "Книги",
    "film": "Фильмы",
    "game": "Игры",
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

FEED_ACTION_LABELS_RU = {
    "added": "Добавлено",
    "planning": "Запланировано",
    "in_progress": "В процессе",
    "completed": "Завершено",
    "dropped": "Брошено",
    "rated": "Оценка",
}

FEED_ACTION_ICONS = {
    "added": "bi bi-plus-circle",
    "planning": "bi bi-clock",
    "in_progress": "bi bi-play-circle",
    "completed": "bi bi-check-circle",
    "dropped": "bi bi-x-circle",
    "rated": "bi bi-star",
}
