"""Tests for apps.vor_archives.dashboard.services.utils."""

from datetime import date

import pytest

from apps.vor_archives.dashboard.services.utils import (
    load_user_works,
    monday,
    sunday,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
)


# ─── monday & sunday ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "day,expected",
    [
        pytest.param(date(2025, 1, 6), date(2025, 1, 6), id="monday"),
        pytest.param(date(2025, 1, 7), date(2025, 1, 6), id="tuesday"),
        pytest.param(date(2025, 1, 12), date(2025, 1, 6), id="sunday"),
    ],
)
def test_monday(day, expected):
    assert monday(day) == expected


@pytest.mark.parametrize(
    "day,expected",
    [
        pytest.param(date(2025, 1, 12), date(2025, 1, 12), id="sunday"),
        pytest.param(date(2025, 1, 11), date(2025, 1, 12), id="saturday"),
        pytest.param(date(2025, 1, 6), date(2025, 1, 12), id="monday"),
    ],
)
def test_sunday(day, expected):
    assert sunday(day) == expected


# ─── load_user_works ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_load_user_works_filters_by_user_and_prefetches_works(
    user, other_user, book, movie, game, django_assert_num_queries
):
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    UserWorkFactory(user=user, work=game)
    UserWorkFactory(user=other_user, work=BookFactory())

    # 1 (UserWork + ContentType) + 3 (Book, Film, Game) = 4 queries
    with django_assert_num_queries(4):
        items = load_user_works(user, with_attrs=False)
        titles = {uw.work.title for uw in items}

    assert titles == {book.title, movie.title, game.title}


@pytest.mark.django_db
def test_load_user_works_with_attrs_prefetches_relations(
    user, book, game, django_assert_num_queries
):
    tag = TagFactory()
    author = PersonFactory()
    book.tags.add(tag)
    book.authors.add(author)
    book.genres.add(BookGenreFactory())

    game.tags.add(tag)
    game.authors.add(author)
    game.platforms.add(PlatformFactory())

    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=game)

    # 1 (UserWork) + 2 (Book, Game) + 2 (tags) + 2 (authors) + 2 (genres) + 1 (platforms) = 10
    with django_assert_num_queries(10):
        items = load_user_works(user, with_attrs=True)
        for uw in items:
            list(uw.work.tags.all())
            list(uw.work.authors.all())
            list(uw.work.genres.all())
            if hasattr(uw.work, "platforms"):
                list(uw.work.platforms.all())

    assert len(items) == 2
