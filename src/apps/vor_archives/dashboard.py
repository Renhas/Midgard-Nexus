from calendar import monthrange
from collections import Counter
from datetime import date, timedelta

from django.db.models import Count, prefetch_related_objects
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from .constants import AgeRatingChoices, FilmTypeChoices, UserWorkStatusChoices
from .models import FeedItem, UserWork
from .templatetags.vor_archives_extras import (
    FEED_ACTION_ICONS,
    FEED_ACTION_LABELS_RU,
    STATUS_LABELS_RU,
)

WORK_TYPES = ("book", "film", "game")
AGE_CHOICES_EXT = [("", "Не указан")] + list(AgeRatingChoices.choices)
RATING_CHOICES_EXT = [("", "Без оценки")] + [
    (str(value), str(value)) for value in range(1, 11)
]

TYPE_META = {
    "book": {"label": "Книги", "icon": "icon-book-text", "unit": "стр."},
    "film": {"label": "Фильмы", "icon": "icon-clapperboard", "unit": "ч."},
    "game": {"label": "Игры", "icon": "icon-gamepad-2", "unit": "ч."},
}

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

WEEKDAY_LABELS = ["Пн", "", "Ср", "", "Пт", "", ""]

FEED_PAGE_SIZE = 30
HIST_TOP_N = 12


def format_number(value):
    number = round(float(value or 0), 1)
    if number == int(number):
        return str(int(number))
    return str(number)


def format_percent(part, total):
    if not total:
        return "0%"
    value = round(part * 100 / total, 1)
    if value == int(value):
        return f"{int(value)}%"
    return f"{value}%"


def percent_value(part, total):
    if not total:
        return 0
    return round(part * 100 / total, 1)


def progress_spent(user_work):
    work = getattr(user_work, "work", None)
    if work is None:
        return None
    progress = float(user_work.progress or 0)
    model_name = work._meta.model_name
    if model_name == "book":
        return ("book", progress, "стр.")
    if model_name == "game":
        return ("game", progress, "ч.")
    if model_name == "film":
        if work.film_type == FilmTypeChoices.TV_SHOW:
            duration = float(work.duration_minutes or 0)
            return ("film", duration * progress / 60.0, "ч.")
        return ("film", progress / 60.0, "ч.")
    return None


def load_user_works(user, with_attrs=False):
    items = list(UserWork.objects.filter(user=user).select_related("work_content_type"))
    prefetch_related_objects(items, "work")
    if with_attrs:
        _prefetch_work_attrs(items)
    return items


def _prefetch_work_attrs(user_works):
    by_type = {key: [] for key in WORK_TYPES}
    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        bucket = by_type.get(work._meta.model_name)
        if bucket is not None:
            bucket.append(work)
    for type_key, works in by_type.items():
        if not works:
            continue
        related = ["tags", "authors", "genres"]
        if type_key == "game":
            related.append("platforms")
        prefetch_related_objects(works, *related)


def _empty_status_matrix():
    return {
        type_key: {status: 0 for status in UserWorkStatusChoices.values}
        for type_key in WORK_TYPES
    }


def _empty_age_matrix():
    return {type_key: {age[0]: 0 for age in AGE_CHOICES_EXT} for type_key in WORK_TYPES}


def _empty_rating_matrix():
    return {
        type_key: {rat[0]: 0 for rat in RATING_CHOICES_EXT} for type_key in WORK_TYPES
    }


def stats_payload(user):
    user_works = load_user_works(user)
    status_matrix = _empty_status_matrix()
    age_matrix = _empty_age_matrix()
    rating_matrix = _empty_rating_matrix()
    spent = {key: 0.0 for key in WORK_TYPES}

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        type_key = work._meta.model_name
        age_key = work.age_rating or ""
        rating_key = str(user_work.rating or "")
        if type_key not in WORK_TYPES:
            continue
        age_matrix[type_key][age_key] += 1
        rating_matrix[type_key][rating_key] += 1
        status_matrix[type_key][user_work.status] += 1
        spent_row = progress_spent(user_work)
        if spent_row:
            spent[spent_row[0]] += spent_row[1]
    return {
        "stats_opts": {
            "status_matrix": status_matrix,
            "age_matrix": age_matrix,
            "rating_matrix": rating_matrix,
            "spent": spent,
            "type_meta": TYPE_META,
            "status_choices": {
                key: {"label": STATUS_LABELS_RU[key]}
                for key in UserWorkStatusChoices.values
            },
            "age_choices": {key: {"label": name} for key, name in AGE_CHOICES_EXT},
            "rating_choices": {
                key: {"label": name} for key, name in RATING_CHOICES_EXT
            },
        },
    }


def _pie_items(counter, labels):
    items = []
    for key, label in labels:
        value = counter.get(key, 0)
        if value:
            items.append({"key": key, "label": label, "value": value})
    return items


def _attrs_to_items(user_works):
    tags = Counter()
    persons = Counter()
    platforms = Counter()
    genres = {key: Counter() for key in WORK_TYPES}

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        for tag in work.tags.all():
            tags[tag.name] += 1
        for person in work.authors.all():
            persons[person.name] += 1
        type_key = work._meta.model_name
        if type_key == "game":
            for platform in work.platforms.all():
                platforms[platform.name] += 1
        if type_key in genres and hasattr(work, "genres"):
            for genre in work.genres.all():
                genres[type_key][genre.name] += 1
    genre_items = []
    for type_key, counter in genres.items():
        for name, count in counter.items():
            genre_items.append(
                {
                    "name": f"{name} ({TYPE_META[type_key]['label']})",
                    "count": count,
                }
            )
    genre_items.sort(key=lambda item: (-item["count"], item["name"]))

    def as_items(counter):
        items = [{"name": name, "count": count} for name, count in counter.items()]
        items.sort(key=lambda item: (-item["count"], item["name"]))
        return items

    return {
        "tags": as_items(tags),
        "genres": genre_items,
        "persons": as_items(persons),
        "platforms": as_items(platforms),
    }


def attrs_payload(user):
    user_works = load_user_works(user, with_attrs=True)

    view_types = [
        {"key": "cloud", "label": "Облако", "icon": "bi bi-cloud"},
        {"key": "bar", "label": "Гистограмма", "icon": "bi bi-bar-chart"},
        {"key": "list", "label": "Список", "icon": "bi bi-list-ul"},
    ]
    attr_kinds = [
        {"key": "tags", "label": "Теги", "icon": "bi bi-tag"},
        {"key": "persons", "label": "Авторы", "icon": "bi bi-person"},
        {"key": "genres", "label": "Жанры", "icon": "icon-drama"},
        {"key": "platforms", "label": "Платформы", "icon": "bi bi-controller"},
    ]
    return {
        "attr_kinds": attr_kinds,
        "view_types": view_types,
        "attrs_opts": {
            "attrs": _attrs_to_items(user_works),
            "total": len(user_works),
            "histTopN": HIST_TOP_N,
        },
    }


def _feed_item_payload(item):
    user_work = item.user_work
    work = getattr(user_work, "work", None) if user_work else None
    work_title = ""
    detail_url = ""
    if work is not None:
        work_title = work.title
        detail_url = reverse("vor_archives:artwork_detail", args=[user_work.pk])
    elif user_work is not None:
        work_title = "Удалённое произведение"
    return {
        "id": item.pk,
        "action_type": item.action_type,
        "label": FEED_ACTION_LABELS_RU.get(
            item.action_type, item.get_action_type_display()
        ),
        "icon": FEED_ACTION_ICONS.get(item.action_type, "bi bi-circle"),
        "timestamp": item.timestamp,
        "work_title": work_title,
        "detail_url": detail_url,
    }


def feed_page(user, offset=0, limit=FEED_PAGE_SIZE):
    qs = (
        FeedItem.objects.filter(user=user)
        .select_related("user_work", "user_work__work_content_type")
        .order_by("-timestamp", "-pk")
    )
    items = list(qs[offset : offset + limit + 1])
    has_more = len(items) > limit
    items = items[:limit]
    prefetch_related_objects(
        [item.user_work for item in items if item.user_work_id],
        "work",
    )
    return [_feed_item_payload(item) for item in items], has_more


def _monday(day):
    return day - timedelta(days=day.weekday())


def _sunday(day):
    return day + timedelta(days=6 - day.weekday())


def _heat_level(count, max_count):
    if count <= 0:
        return 0
    if max_count <= 1:
        return 4
    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def _heat_title(day, count):
    label = day.strftime("%d.%m.%Y")
    if count <= 0:
        return f"Нет активности — {label}"
    return f"{count} — {label}"


def activity_years(user):
    timestamps = FeedItem.objects.filter(user=user).values_list("timestamp", flat=True)
    years = sorted({timezone.localtime(value).year for value in timestamps})
    today_year = timezone.localdate().year
    if today_year not in years:
        years.append(today_year)
        years.sort()
    if not years:
        years = [today_year]
    return years


def heatmap_range(year=None, today=None):
    today = today or timezone.localdate()
    if year is None:
        start = today - timedelta(days=365)
        end = today
    else:
        start = date(year, 1, 1)
        end = date(year, 12, monthrange(year, 12)[1])
    return start, end, _monday(start), _sunday(end)


def heatmap_payload(user, year=None, today=None):
    today = today or timezone.localdate()
    start, end, grid_start, grid_end = heatmap_range(year, today=today)
    tz = timezone.get_current_timezone()
    rows = (
        FeedItem.objects.filter(
            user=user,
            timestamp__date__gte=start,
            timestamp__date__lte=end,
        )
        .annotate(day=TruncDate("timestamp", tzinfo=tz))
        .values("day")
        .annotate(n=Count("id"))
    )
    counts = {}
    for row in rows:
        day = row["day"]
        if day is None:
            continue
        counts[day] = row["n"]
    max_count = max(counts.values(), default=0)

    weeks = []
    cursor = grid_start
    while cursor <= grid_end:
        week = []
        for _ in range(7):
            in_range = start <= cursor <= end
            count = counts.get(cursor, 0) if in_range else 0
            week.append(
                {
                    "date": cursor.isoformat(),
                    "count": count,
                    "level": _heat_level(count, max_count) if in_range else 0,
                    "in_range": in_range,
                    "title": _heat_title(cursor, count) if in_range else "",
                }
            )
            cursor += timedelta(days=1)
        weeks.append(week)

    month_labels = []
    prev_month = None
    for week in weeks:
        in_days = [date.fromisoformat(day["date"]) for day in week if day["in_range"]]
        if not in_days:
            month_labels.append("")
            continue
        month = in_days[0].month
        if month != prev_month:
            month_labels.append(MONTHS_RU[month])
            prev_month = month
        else:
            month_labels.append("")

    return {
        "year": year,
        "years": activity_years(user),
        "weeks": weeks,
        "month_labels": month_labels,
        "weekday_labels": WEEKDAY_LABELS,
        "max_count": max_count,
    }


def parse_heatmap_year(raw):
    value = (raw or "").strip()
    if not value:
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    if year < 1970 or year > 2100:
        return None
    return year
