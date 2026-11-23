from calendar import monthrange
from datetime import date, timedelta

from django.db.models import Count, prefetch_related_objects
from django.db.models.functions import ExtractYear, TruncDate
from django.urls import reverse
from django.utils import timezone

from apps.vor_archives.constants import get_feed_action_meta
from apps.vor_archives.models import FeedItem

from ..catalog import (
    DAYS_IN_WEEK,
    FEED_PAGE_SIZE,
    HEAT_RATIO_THRESHOLDS,
    MONTHS_RU,
    ROLLING_DAYS,
    WEEKDAY_LABELS,
)
from ..forms import HeatmapFilterForm
from .utils import monday, sunday


def _feed_item_payload(item: FeedItem) -> dict:
    user_work = item.user_work
    work = getattr(user_work, "work", None) if user_work else None
    work_title = ""
    detail_url = ""
    if work is not None:
        work_title = work.title
        detail_url = reverse("vor_archives:artworks:detail", args=[user_work.pk])
    meta = get_feed_action_meta(item.action_type)
    return {
        "id": item.pk,
        "action_type": item.action_type,
        "label": meta.label,
        "icon": meta.icon,
        "timestamp": item.timestamp,
        "work_title": work_title,
        "detail_url": detail_url,
    }


def feed_page(
    user, offset: int = 0, limit: int = FEED_PAGE_SIZE
) -> tuple[list[dict], bool]:
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


def feed_context(user, offset: int = 0, limit: int = FEED_PAGE_SIZE) -> dict:
    items, has_more = feed_page(user, offset=offset, limit=limit)
    return {
        "feed_items": items,
        "feed_has_more": has_more,
        "feed_next_offset": offset + len(items),
    }


def heat_level(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 1:
        return len(HEAT_RATIO_THRESHOLDS) + 1
    ratio = count / max_count
    for level, threshold in enumerate(HEAT_RATIO_THRESHOLDS, start=1):
        if ratio <= threshold:
            return level
    return len(HEAT_RATIO_THRESHOLDS) + 1


def _heat_title(day: date, count: int) -> str:
    label = day.strftime("%d.%m.%Y")
    if count <= 0:
        return f"Нет активности — {label}"
    return f"{count} — {label}"


def activity_years(user) -> list[int]:
    tz = timezone.get_current_timezone()
    years_qs = (
        FeedItem.objects.filter(user=user)
        .annotate(year=ExtractYear("timestamp", tzinfo=tz))
        .values_list("year", flat=True)
        .distinct()
    )
    years = {year for year in years_qs if year is not None}
    years.add(timezone.localdate().year)
    return sorted(years)


def heatmap_range(
    year: int | None = None, today: date | None = None
) -> tuple[date, date, date, date]:
    today = today or timezone.localdate()
    if year is None:
        start = today - timedelta(days=ROLLING_DAYS)
        end = today
    else:
        start = date(year, 1, 1)
        end = date(year, 12, monthrange(year, 12)[1])
    return start, end, monday(start), sunday(end)


def _daily_activity_counts(user, start: date, end: date, tz) -> dict[date, int]:
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
    return {row["day"]: row["n"] for row in rows if row["day"] is not None}


def _build_heatmap_weeks(
    start: date,
    end: date,
    grid_start: date,
    grid_end: date,
    counts: dict[date, int],
    max_count: int,
) -> list[list[dict]]:
    weeks: list[list[dict]] = []
    cursor = grid_start
    while cursor <= grid_end:
        week: list[dict] = []
        for _ in range(DAYS_IN_WEEK):
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
    return weeks


def _build_month_labels(weeks: list[list[dict]]) -> list[str]:
    month_labels: list[str] = []
    for index, week in enumerate(weeks):
        in_days = [date.fromisoformat(day["date"]) for day in week if day["in_range"]]
        if not in_days:
            month_labels.append("")
            continue
        first_of_month = next((d for d in in_days if d.day == 1), None)
        if first_of_month:
            month_labels.append(MONTHS_RU[first_of_month.month])
        elif index == 0:
            month_labels.append(MONTHS_RU[in_days[0].month])
        else:
            month_labels.append("")
    return month_labels


def heatmap_payload(user, year: int | None = None, today: date | None = None) -> dict:
    today = today or timezone.localdate()
    start, end, grid_start, grid_end = heatmap_range(year, today=today)
    tz = timezone.get_current_timezone()
    counts = _daily_activity_counts(user, start, end, tz)
    max_count = max(counts.values(), default=0)
    weeks = _build_heatmap_weeks(start, end, grid_start, grid_end, counts, max_count)

    return {
        "year": year,
        "years": activity_years(user),
        "weeks": weeks,
        "month_labels": _build_month_labels(weeks),
        "weekday_labels": WEEKDAY_LABELS,
        "max_count": max_count,
    }


def activity_context(user, query_params) -> dict:
    year = HeatmapFilterForm(query_params).get_year()
    return {
        **feed_context(user),
        "heatmap": heatmap_payload(user, year=year),
    }
