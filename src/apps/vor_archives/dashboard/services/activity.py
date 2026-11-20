from calendar import monthrange
from datetime import date, timedelta

from django.db.models import Count, prefetch_related_objects
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from apps.vor_archives.constants import FEED_ACTION_ICONS, FEED_ACTION_LABELS_RU
from apps.vor_archives.models import FeedItem

from ..catalog import FEED_PAGE_SIZE, MONTHS_RU, WEEKDAY_LABELS
from .utils import monday, sunday


def _feed_item_payload(item):
    user_work = item.user_work
    work = getattr(user_work, "work", None) if user_work else None
    work_title = ""
    detail_url = ""
    if work is not None:
        work_title = work.title
        detail_url = reverse("vor_archives:artworks:detail", args=[user_work.pk])
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


def heat_level(count, max_count):
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
    return start, end, monday(start), sunday(end)


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
                    "level": heat_level(count, max_count) if in_range else 0,
                    "in_range": in_range,
                    "title": _heat_title(cursor, count) if in_range else "",
                }
            )
            cursor += timedelta(days=1)
        weeks.append(week)

    month_labels = []
    for i, week in enumerate(weeks):
        in_days = [date.fromisoformat(day["date"]) for day in week if day["in_range"]]
        if not in_days:
            month_labels.append("")
            continue

        first_of_month = next((d for d in in_days if d.day == 1), None)
        if first_of_month:
            month_labels.append(MONTHS_RU[first_of_month.month])
        elif i == 0:
            month_labels.append(MONTHS_RU[in_days[0].month])
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
