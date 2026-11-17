"""Tests for sorting functions in apps.vor_archives.artworks.services.queries."""

from datetime import datetime, timezone as dt_timezone

import pytest

from apps.vor_archives.artworks.services.queries import sort_user_works
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    FilmFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

# ─── sort_user_works ─────────────────────────────────────────────────────────


def test_sort_user_works_by_title_ascending(user):
    book = BookFactory(title="Alpha")
    film = FilmFactory(title="Zeta")
    uw_book = UserWorkFactory(user=user, work=book)
    uw_film = UserWorkFactory(user=user, work=film)

    result = sort_user_works([uw_film, uw_book], {"sort": "title", "sort_asc": True})

    assert result == [uw_book, uw_film]


def test_sort_user_works_by_title_descending(user):
    book = BookFactory(title="Alpha")
    film = FilmFactory(title="Zeta")
    uw_book = UserWorkFactory(user=user, work=book)
    uw_film = UserWorkFactory(user=user, work=film)

    result = sort_user_works([uw_book, uw_film], {"sort": "title", "sort_asc": False})

    assert result == [uw_film, uw_book]


def test_sort_user_works_by_title_case_insensitive(user):
    lower = BookFactory(title="apple")
    upper = BookFactory(title="Banana")
    uw_lower = UserWorkFactory(user=user, work=lower)
    uw_upper = UserWorkFactory(user=user, work=upper)

    result = sort_user_works([uw_upper, uw_lower], {"sort": "title", "sort_asc": True})

    assert result == [uw_lower, uw_upper]


def test_sort_user_works_by_rating_puts_unrated_last_ascending(user):
    book = BookFactory()
    film = FilmFactory()
    uw_rated = UserWorkFactory(user=user, work=book, rating=5)
    uw_unrated = UserWorkFactory(user=user, work=film, rating=None)

    result = sort_user_works(
        [uw_unrated, uw_rated], {"sort": "rating", "sort_asc": True}
    )

    assert result == [uw_rated, uw_unrated]


def test_sort_user_works_by_rating_descending(user):
    low = UserWorkFactory(user=user, work=BookFactory(), rating=3)
    high = UserWorkFactory(user=user, work=BookFactory(), rating=9)

    result = sort_user_works([low, high], {"sort": "rating", "sort_asc": False})

    assert result == [high, low]


def test_sort_user_works_by_status_uses_defined_order(user):
    uw_planning = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.PLANNING
    )
    uw_progress = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.IN_PROGRESS
    )
    uw_done = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.COMPLETED
    )

    result = sort_user_works(
        [uw_done, uw_planning, uw_progress],
        {"sort": "status", "sort_asc": True},
    )

    assert result == [uw_planning, uw_progress, uw_done]


def test_sort_user_works_by_status_unknown_goes_last(user):
    uw_known = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.PLANNING
    )
    uw_known_2 = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.DROPPED
    )
    UserWork.objects.filter(pk=uw_known_2.pk).update(status="mystery")
    uw_known_2.refresh_from_db()

    result = sort_user_works(
        [uw_known_2, uw_known], {"sort": "status", "sort_asc": True}
    )

    assert result == [uw_known, uw_known_2]


def test_sort_user_works_by_date_added(user):
    uw_first = UserWorkFactory(user=user, work=BookFactory())
    uw_second = UserWorkFactory(user=user, work=BookFactory())
    UserWork.objects.filter(pk=uw_first.pk).update(
        date_added=datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
    )
    UserWork.objects.filter(pk=uw_second.pk).update(
        date_added=datetime(2024, 1, 2, tzinfo=dt_timezone.utc)
    )
    uw_first.refresh_from_db()
    uw_second.refresh_from_db()

    result = sort_user_works(
        [uw_second, uw_first], {"sort": "date_added", "sort_asc": True}
    )

    assert result == [uw_first, uw_second]


def test_sort_user_works_by_custom_position(user):
    uw_book = UserWorkFactory(user=user, work=BookFactory())
    uw_film = UserWorkFactory(user=user, work=FilmFactory())
    UserWork.objects.filter(pk=uw_book.pk).update(order_position=1)
    UserWork.objects.filter(pk=uw_film.pk).update(order_position=0)
    uw_book.refresh_from_db()
    uw_film.refresh_from_db()

    result = sort_user_works([uw_book, uw_film], {"sort": "custom"})

    assert result == [uw_film, uw_book]


def test_sort_user_works_uses_order_key_when_provided(user):
    uw_a = UserWorkFactory(user=user, work=BookFactory())
    uw_b = UserWorkFactory(user=user, work=BookFactory())

    result = sort_user_works(
        [uw_b, uw_a], {"sort": "custom"}, order_key=lambda uw: uw.pk
    )

    assert result == sorted([uw_a, uw_b], key=lambda uw: uw.pk)


def test_sort_user_works_default_is_custom(user):
    uw_a = UserWorkFactory(user=user, work=BookFactory())
    uw_b = UserWorkFactory(user=user, work=BookFactory())
    UserWork.objects.filter(pk=uw_a.pk).update(order_position=1)
    UserWork.objects.filter(pk=uw_b.pk).update(order_position=0)
    uw_a.refresh_from_db()
    uw_b.refresh_from_db()

    result = sort_user_works([uw_a, uw_b], {})

    assert result == [uw_b, uw_a]
