from apps.vor_archives.constants import AgeRatingChoices
from apps.vor_archives.registry import (
    WORK_TYPE_ICONS,
    WORK_TYPE_LABELS_PLURAL,
    WORK_TYPE_UNITS,
    WORK_TYPES,
)

DASHBOARD_TABS = [
    {"kind": "stats", "label": "Статистика", "icon": "bi bi-pie-chart"},
    {"kind": "attrs", "label": "Аттрибуты", "icon": "bi bi-cloud"},
    {"kind": "activity", "label": "Активность", "icon": "bi bi-calendar-date"},
]

DEFAULT_DASH_TAB = "stats"

DASH_TAB_KINDS = {tab["kind"] for tab in DASHBOARD_TABS}

AGE_CHOICES_EXT = [("", "Не указан")] + list(AgeRatingChoices.choices)
RATING_CHOICES_EXT = [("", "Без оценки")] + [
    (str(value), str(value)) for value in range(1, 11)
]

TYPE_META = {
    key: {
        "label": WORK_TYPE_LABELS_PLURAL[key],
        "icon": WORK_TYPE_ICONS[key],
        "unit": WORK_TYPE_UNITS[key],
    }
    for key in WORK_TYPES
}

ATTR_VIEW_TYPES = [
    {"key": "cloud", "label": "Облако", "icon": "bi bi-cloud"},
    {"key": "bar", "label": "Гистограмма", "icon": "bi bi-bar-chart"},
    {"key": "list", "label": "Список", "icon": "bi bi-list-ul"},
]

ATTR_KINDS = [
    {"key": "tags", "label": "Теги", "icon": "bi bi-tag"},
    {"key": "persons", "label": "Авторы", "icon": "bi bi-person"},
    {"key": "genres", "label": "Жанры", "icon": "icon-drama"},
    {"key": "platforms", "label": "Платформы", "icon": "bi bi-controller"},
]

MONTHS_RU = {
    1: "Янв",
    2: "Фев",
    3: "Мар",
    4: "Апр",
    5: "Май",
    6: "Июн",
    7: "Июл",
    8: "Авг",
    9: "Сен",
    10: "Окт",
    11: "Ноя",
    12: "Дек",
}

WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

FEED_PAGE_SIZE = 30
HIST_TOP_N = 12


def get_dash_tab(kind):
    for tab in DASHBOARD_TABS:
        if tab["kind"] == kind:
            return tab
    return None
