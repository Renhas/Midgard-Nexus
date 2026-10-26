from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import (
    Book,
    Film,
    Game,
)

WORK_MODELS = {
    "book": Book,
    "film": Film,
    "game": Game,
}

STATUS_SORT_ORDER = {
    UserWorkStatusChoices.PLANNING: 0,
    UserWorkStatusChoices.IN_PROGRESS: 1,
    UserWorkStatusChoices.COMPLETED: 2,
    UserWorkStatusChoices.DROPPED: 3,
}

WORK_TYPE_ICONS = {
    "book": "icon-book-text",
    "film": "icon-clapperboard",
    "game": "icon-gamepad-2",
}
