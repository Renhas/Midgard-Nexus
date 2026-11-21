from typing import TypedDict

from apps.vor_archives.constants import AgeRatingChoices
from apps.vor_archives.registry import (
    ATTRIBUTE_KIND_REGISTRY,
    WORK_TYPE_REGISTRY,
)


class DashboardTab(TypedDict):
    kind: str
    label: str
    icon: str


class AttrKindOption(TypedDict):
    key: str
    label: str
    icon: str


DASHBOARD_TABS: tuple[DashboardTab, ...] = (
    {"kind": "stats", "label": "Статистика", "icon": "bi bi-pie-chart"},
    {"kind": "attrs", "label": "Аттрибуты", "icon": "bi bi-cloud"},
    {"kind": "activity", "label": "Активность", "icon": "bi bi-calendar-date"},
)

DASHBOARD_TAB_MAP: dict[str, DashboardTab] = {
    tab["kind"]: tab for tab in DASHBOARD_TABS
}

DEFAULT_DASH_TAB = "stats"

DASH_TAB_KINDS = set(DASHBOARD_TAB_MAP)

RATING_MIN = 1
RATING_MAX = 10

AGE_CHOICES_EXT: list[tuple[str, str]] = [("", "Не указан"), *AgeRatingChoices.choices]
RATING_CHOICES_EXT: list[tuple[str, str]] = [
    ("", "Без оценки"),
    *((str(value), str(value)) for value in range(RATING_MIN, RATING_MAX + 1)),
]

TYPE_META = {
    key: {
        "label": meta.label_plural,
        "icon": meta.icon,
        "unit": meta.unit,
    }
    for key, meta in WORK_TYPE_REGISTRY.items()
}

ATTR_VIEW_TYPES: tuple[AttrKindOption, ...] = (
    {"key": "cloud", "label": "Облако", "icon": "bi bi-cloud"},
    {"key": "bar", "label": "Гистограмма", "icon": "bi bi-bar-chart"},
    {"key": "list", "label": "Список", "icon": "bi bi-list-ul"},
)

ATTR_KINDS: list[AttrKindOption] = [
    {
        "key": meta.key,
        "label": meta.label,
        "icon": meta.icon,
    }
    for meta in ATTRIBUTE_KIND_REGISTRY.values()
]

MONTH_LABELS_RU: tuple[str, ...] = (
    "Янв",
    "Фев",
    "Мар",
    "Апр",
    "Май",
    "Июн",
    "Июл",
    "Авг",
    "Сен",
    "Окт",
    "Ноя",
    "Дек",
)

MONTHS_RU: dict[int, str] = {
    index: label for index, label in enumerate(MONTH_LABELS_RU, start=1)
}

WEEKDAY_LABELS: tuple[str, ...] = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")

ROLLING_DAYS = 365
DAYS_IN_WEEK = 7
HEATMAP_MIN_YEAR = 1970
HEATMAP_MAX_YEAR = 2100
HEAT_RATIO_THRESHOLDS: tuple[float, ...] = (0.25, 0.5, 0.75)

FEED_PAGE_SIZE = 30
HIST_TOP_N = 12


def get_dash_tab(kind: str) -> DashboardTab | None:
    return DASHBOARD_TAB_MAP.get(kind)
