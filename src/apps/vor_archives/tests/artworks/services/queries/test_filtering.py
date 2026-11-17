"""Tests for filtering functions in apps.vor_archives.artworks.services.queries."""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services.queries import load_filtered_user_works
from apps.vor_archives.constants import AgeRatingChoices, UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmFactory,
    GameFactory,
    PlatformFactory,
    UserWorkFactory,
)
from apps.vor_archives.tests.conftest import ALL_STATUSES

pytestmark = pytest.mark.django_db

# ─── load_filtered_user_works ────────────────────────────────────────────────


def test_load_filtered_user_works_empty_without_types(user, book):
    UserWorkFactory(user=user, work=book)

    assert load_filtered_user_works(user, {}) == []
    assert load_filtered_user_works(user, {"types": []}) == []
    assert load_filtered_user_works(user, {"types": ["unknown"]}) == []


def test_load_filtered_user_works_by_type(user, book, movie):
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == book.pk


def test_load_filtered_user_works_excludes_other_users(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    assert load_filtered_user_works(user, {"types": ["book"]}) == []


def test_load_filtered_user_works_filters_by_status(user):
    uw_done = UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.COMPLETED
    )
    UserWorkFactory(
        user=user, work=FilmFactory(), status=UserWorkStatusChoices.PLANNING
    )

    result = load_filtered_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": [UserWorkStatusChoices.COMPLETED],
        },
    )

    assert result == [uw_done]


def test_load_filtered_user_works_skips_status_filter_when_all_selected(user):
    UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.COMPLETED
    )
    UserWorkFactory(
        user=user, work=BookFactory(), status=UserWorkStatusChoices.PLANNING
    )
    all_statuses = list(UserWorkStatusChoices.values)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": all_statuses,
            "all_statuses": all_statuses,
        },
    )

    assert len(result) == 2


def test_load_filtered_user_works_empty_statuses_returns_nothing(user, book):
    UserWorkFactory(user=user, work=book)

    result = load_filtered_user_works(user, {"types": ["book"], "statuses": []})

    assert result == []


def test_load_filtered_user_works_hides_when_show_hidden_false(user, book):
    UserWorkFactory(user=user, work=book, is_hidden=True)

    base = {
        "types": ["book"],
        "statuses": ALL_STATUSES,
        "all_statuses": ALL_STATUSES,
    }

    assert load_filtered_user_works(user, {**base, "show_hidden": False}) == []
    assert len(load_filtered_user_works(user, {**base, "show_hidden": True})) == 1


def test_load_filtered_user_works_includes_hidden_by_default(user, book):
    UserWorkFactory(user=user, work=book, is_hidden=True)

    assert (
        len(
            load_filtered_user_works(
                user,
                {
                    "types": ["book"],
                    "statuses": ALL_STATUSES,
                    "all_statuses": ALL_STATUSES,
                },
            )
        )
        == 1
    )


def test_load_filtered_user_works_filters_by_age_rating(user):
    book = BookFactory(age_rating=AgeRatingChoices.RATING_0)
    film = FilmFactory(age_rating=AgeRatingChoices.RATING_18)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=film)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "age_ratings": [AgeRatingChoices.RATING_0],
            "all_age_ratings": [
                AgeRatingChoices.RATING_0,
                AgeRatingChoices.RATING_18,
            ],
        },
    )

    assert len(result) == 1
    assert result[0].work.age_rating == AgeRatingChoices.RATING_0


def test_load_filtered_user_works_filters_by_tag(user):
    from apps.vor_archives.tests.factories import TagFactory

    tag_match = TagFactory()
    tag_other = TagFactory()
    book = BookFactory()
    book.tags.add(tag_match)
    film = FilmFactory()
    film.tags.add(tag_other)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=film)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "tags": [tag_match.pk],
            "all_tags": [tag_match.pk, tag_other.pk],
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == book.pk


def test_load_filtered_user_works_filters_by_book_genre(user):
    genre_match = BookGenreFactory()
    genre_other = BookGenreFactory()
    book = BookFactory()
    book.genres.add(genre_match)
    film = FilmFactory()
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=film)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "genre_book": [genre_other.pk],
            "all_genre_book": [genre_match.pk, genre_other.pk],
        },
    )

    assert result == []


def test_load_filtered_user_works_filters_by_platform(user):
    platform_match = PlatformFactory()
    platform_other = PlatformFactory()
    game = GameFactory()
    game.platforms.add(platform_match)
    UserWorkFactory(user=user, work=game)

    result = load_filtered_user_works(
        user,
        {
            "types": ["game"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "platforms": [platform_other.pk],
            "all_platforms": [platform_match.pk, platform_other.pk],
        },
    )

    assert result == []


def test_load_filtered_user_works_no_filter_when_selection_matches_all(user, book):
    tag = BookFactory().tags  # noqa: F841 - check empty case
    genre = BookGenreFactory()
    book.genres.add(genre)
    UserWorkFactory(user=user, work=book)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "genre_book": [genre.pk],
            "all_genre_book": [genre.pk],
        },
    )

    assert len(result) == 1


def test_load_filtered_user_works_skips_dangling_work(user, book):
    uw = UserWorkFactory(user=user, work=book)
    UserWork.objects.filter(pk=uw.pk).update(work_object_id=999999)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert result == []


def test_load_filtered_user_works_keeps_matching_genre(user):
    genre = BookGenreFactory()
    book = BookFactory()
    book.genres.add(genre)
    other = BookGenreFactory()
    UserWorkFactory(user=user, work=book)

    result = load_filtered_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "genre_book": [genre.pk],
            "all_genre_book": [genre.pk, other.pk],
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == book.pk


def test_load_filtered_user_works_keeps_matching_platform(user):
    platform = PlatformFactory()
    game = GameFactory()
    game.platforms.add(platform)
    UserWorkFactory(user=user, work=game)

    result = load_filtered_user_works(
        user,
        {
            "types": ["game"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "platforms": [platform.pk],
            "all_platforms": [platform.pk],
        },
    )

    assert len(result) == 1
