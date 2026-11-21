"""Tests for apps.vor_archives.dashboard.services.activity and utils."""

from datetime import date, datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import FEED_ACTION_ICONS, FEED_ACTION_LABELS_RU
from apps.vor_archives.dashboard.services.activity import (
    activity_years,
    feed_page,
    heat_level,
    heatmap_payload,
    heatmap_range,
)
from apps.vor_archives.models import FeedItem
from apps.vor_archives.tests.factories import BookFactory, UserWorkFactory


def _set_timestamp(item, when):
    FeedItem.objects.filter(pk=item.pk).update(timestamp=when)
    item.refresh_from_db()
    return item


@pytest.mark.django_db
def test_feed_page_orders_and_paginates(user, book, movie):
    first = UserWorkFactory(user=user, work=book)
    second = UserWorkFactory(user=user, work=movie)
    older = FeedItem.objects.filter(user_work=first, action_type="added").get()
    newer = FeedItem.objects.filter(user_work=second, action_type="added").get()
    _set_timestamp(older, timezone.now() - timedelta(hours=2))
    _set_timestamp(newer, timezone.now() - timedelta(hours=1))

    page, has_more = feed_page(user, offset=0, limit=1)

    assert has_more is True
    assert page[0]["work_title"] == movie.title
    assert page[0]["detail_url"] == reverse(
        "vor_archives:artworks:detail", args=[second.pk]
    )
    assert page[0]["label"] == FEED_ACTION_LABELS_RU["added"]
    assert page[0]["icon"] == FEED_ACTION_ICONS["added"]

    rest, rest_more = feed_page(user, offset=1, limit=1)
    assert rest[0]["work_title"] == book.title
    assert rest[0]["detail_url"] == reverse(
        "vor_archives:artworks:detail", args=[first.pk]
    )
    assert rest_more is False


@pytest.mark.django_db
def test_feed_page_tie_breaks_by_pk_desc(user, book, movie):
    first = UserWorkFactory(user=user, work=book)
    second = UserWorkFactory(user=user, work=movie)
    item_a = FeedItem.objects.filter(user_work=first, action_type="added").get()
    item_b = FeedItem.objects.filter(user_work=second, action_type="added").get()

    same_time = timezone.now() - timedelta(hours=1)
    _set_timestamp(item_a, same_time)
    _set_timestamp(item_b, same_time)

    page, _ = feed_page(user, limit=2)

    assert page[0]["id"] == item_b.pk
    assert page[1]["id"] == item_a.pk


@pytest.mark.django_db
def test_feed_page_filters_by_user(user, book):
    UserWorkFactory(user=user, work=book)
    other = UserFactory()
    other_book = BookFactory()
    UserWorkFactory(user=other, work=other_book)

    page, has_more = feed_page(user)

    assert len(page) == 1
    assert page[0]["work_title"] == book.title
    assert has_more is False


@pytest.mark.django_db
def test_feed_page_empty(user):
    page, has_more = feed_page(user)

    assert page == []
    assert has_more is False


@pytest.mark.django_db
def test_feed_item_payload_with_deleted_user_work(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    user_work.delete()

    page, _ = feed_page(user)

    assert len(page) == 1
    assert page[0]["work_title"] == ""
    assert page[0]["detail_url"] == ""


@pytest.mark.django_db
def test_heatmap_payload_grid_structure(user):
    payload = heatmap_payload(user, year=2024)

    assert list(payload["weekday_labels"]) == ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    assert all(len(week) == 7 for week in payload["weeks"])
    assert len(payload["month_labels"]) == len(payload["weeks"])


@pytest.mark.django_db
def test_heatmap_counts_days_in_selected_year(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.filter(user_work=user_work).get()
    when = timezone.make_aware(datetime(2024, 3, 15, 12, 0))
    _set_timestamp(item, when)

    payload = heatmap_payload(user, year=2024)
    counted = [day for week in payload["weeks"] for day in week if day["count"]]

    assert payload["year"] == 2024
    assert len(counted) == 1
    assert counted[0]["date"] == "2024-03-15"
    assert counted[0]["count"] == 1


@pytest.mark.django_db
def test_heatmap_payload_default_range_is_last_year(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.get(user_work=user_work)
    _set_timestamp(item, timezone.make_aware(datetime(2024, 3, 15, 12, 0)))

    payload = heatmap_payload(user, today=date(2024, 6, 1))

    assert payload["year"] is None
    counted = [day for week in payload["weeks"] for day in week if day["count"]]
    assert counted[0]["date"] == "2024-03-15"


@pytest.mark.django_db
def test_heatmap_payload_excludes_other_years(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.get(user_work=user_work)
    _set_timestamp(item, timezone.make_aware(datetime(2023, 3, 15, 12, 0)))

    payload = heatmap_payload(user, year=2024)
    counted = [day for week in payload["weeks"] for day in week if day["count"]]

    assert counted == []
    assert payload["max_count"] == 0


@pytest.mark.django_db
def test_heatmap_payload_years_deduped_and_sorted(user):
    for _ in range(2):
        uw = UserWorkFactory(user=user, work=BookFactory())
        item = FeedItem.objects.get(user_work=uw, action_type="added")
        _set_timestamp(item, timezone.make_aware(datetime(2020, 5, 1, 12, 0)))

    for _ in range(2):
        UserWorkFactory(user=user, work=BookFactory())

    payload = heatmap_payload(user)

    assert payload["years"] == [2020, timezone.localdate().year]


@pytest.mark.django_db
def test_heatmap_payload_is_user_scoped(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    payload = heatmap_payload(user)

    assert payload["max_count"] == 0
    counted = [day for week in payload["weeks"] for day in week if day["count"]]
    assert counted == []


def test_heatmap_range_for_year():
    start, end, grid_start, grid_end = heatmap_range(2025)

    assert start == date(2025, 1, 1)
    assert end == date(2025, 12, 31)
    assert grid_start == date(2024, 12, 30)
    assert grid_end == date(2026, 1, 4)


def test_heatmap_range_rolling_365_days():
    today = date(2025, 5, 15)
    start, end, grid_start, grid_end = heatmap_range(None, today=today)

    assert end == today
    assert start == date(2024, 5, 15)
    assert grid_start.weekday() == 0
    assert grid_start <= start
    assert grid_end.weekday() == 6
    assert grid_end >= end


@pytest.mark.django_db
def test_activity_years_empty_defaults_to_current_year(user):
    assert activity_years(user) == [timezone.localdate().year]


@pytest.mark.django_db
def test_heatmap_month_labels_and_cell_titles(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.get(user_work=user_work)
    _set_timestamp(item, timezone.make_aware(datetime(2025, 1, 10, 12, 0)))

    payload = heatmap_payload(user, year=2025)

    assert payload["month_labels"][0] == "Янв"
    non_empty_months = [m for m in payload["month_labels"] if m]
    assert non_empty_months == [
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
    ]

    first_week = payload["weeks"][0]
    out_of_range_cell = first_week[0]  # 2024-12-30 (Пн)
    assert out_of_range_cell["date"] == "2024-12-30"
    assert out_of_range_cell["in_range"] is False
    assert out_of_range_cell["title"] == ""

    empty_jan_cell = first_week[2]  # 2025-01-01 (Ср)
    assert empty_jan_cell["date"] == "2025-01-01"
    assert empty_jan_cell["in_range"] is True
    assert empty_jan_cell["title"] == "Нет активности — 01.01.2025"

    active_cell = next(
        day for week in payload["weeks"] for day in week if day["date"] == "2025-01-10"
    )
    assert active_cell["title"] == "1 — 10.01.2025"


@pytest.mark.django_db
def test_feed_page_exact_limit_has_no_more(user, book, movie, game):
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    UserWorkFactory(user=user, work=game)

    page, has_more = feed_page(user, offset=0, limit=3)

    assert len(page) == 3
    assert has_more is False


@pytest.mark.parametrize(
    "count, max_count, expected",
    [
        (0, 0, 0),
        (0, 12, 0),
        (-1, 10, 0),
        (1, 1, 4),
        (5, 1, 4),
        (1, 0, 4),
        (3, 12, 1),
        (4, 12, 2),
        (6, 12, 2),
        (7, 12, 3),
        (9, 12, 3),
        (10, 12, 4),
        (12, 12, 4),
    ],
)
def test_heat_level(count, max_count, expected):
    assert heat_level(count, max_count) == expected
