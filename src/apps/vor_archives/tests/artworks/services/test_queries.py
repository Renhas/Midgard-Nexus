"""Tests for apps.vor_archives.artworks.services.queries."""

from datetime import datetime, timezone as dt_timezone

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services.queries import (
    load_filtered_user_works,
    search_library_works,
    search_works,
    sort_user_works,
)
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
from ...conftest import ALL_STATUSES

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


# ─── search_works ────────────────────────────────────────────────────────────


def test_search_works_empty_query_returns_empty():
    assert search_works("") == []
    assert search_works("   ") == []
    assert search_works(None) == []


def test_search_works_finds_by_partial_title():
    book = BookFactory(title="Foundation")

    results = search_works("found")

    assert any(r["type_key"] == "book" and r["work_id"] == book.pk for r in results)


def test_search_works_result_shape():
    BookFactory(title="Unique Title")

    results = search_works("Unique")

    assert len(results) >= 1
    assert set(results[0].keys()) == {
        "type_key",
        "work_id",
        "title",
        "cover_url",
        "icon",
    }


def test_search_works_excludes_specific_id():
    book = BookFactory(title="Foundation")

    results = search_works("Found", exclude_type="book", exclude_id=book.pk)

    assert all(r["work_id"] != book.pk for r in results if r["type_key"] == "book")


def test_search_works_exclude_id_as_empty_string_is_ignored():
    book = BookFactory(title="Foundation")

    results = search_works("Found", exclude_type="book", exclude_id="")

    assert any(r["work_id"] == book.pk for r in results if r["type_key"] == "book")


def test_search_works_exclude_without_type_is_ignored():
    book = BookFactory(title="Foundation")

    results = search_works("Found", exclude_type=None, exclude_id=book.pk)

    assert any(r["work_id"] == book.pk for r in results if r["type_key"] == "book")


def test_search_works_respects_limit():
    for i in range(25):
        BookFactory(title=f"Match item {i:03d}")

    results = search_works("Match", limit=10)

    assert len(results) == 10


def test_search_works_sorted_by_title_case_insensitive():
    BookFactory(title="banana")
    BookFactory(title="Apple")
    BookFactory(title="Cherry")

    results = search_works("a")
    titles = [r["title"] for r in results]

    assert titles == sorted(titles, key=str.casefold)


def test_search_works_searches_all_types():
    BookFactory(title="Cross Media")
    FilmFactory(title="Cross Media Film")
    GameFactory(title="Cross Media Game")

    results = search_works("Cross Media")
    type_keys = {r["type_key"] for r in results}

    assert {"book", "film", "game"}.issubset(type_keys)


# ─── search_library_works ────────────────────────────────────────────────────


def test_search_library_works_empty_query(user):
    assert search_library_works(user, "") == {"owned": [], "other": []}
    assert search_library_works(user, "   ") == {"owned": [], "other": []}
    assert search_library_works(user, None) == {"owned": [], "other": []}


def test_search_library_works_separates_owned_and_other(user):
    owned_book = BookFactory(title="Match owned")
    UserWorkFactory(user=user, work=owned_book)
    BookFactory(title="Match other")

    result = search_library_works(user, "Match")

    assert len(result["owned"]) == 1
    assert len(result["other"]) == 1
    assert result["owned"][0]["work_id"] == owned_book.pk
    assert "uw_id" in result["owned"][0]
    assert "uw_id" not in result["other"][0]


def test_search_library_works_does_not_leak_other_users(user):
    other = UserFactory()
    foreign_book = BookFactory(title="Match foreign")
    UserWorkFactory(user=other, work=foreign_book)

    result = search_library_works(user, "Match")

    assert result["owned"] == []
    assert len(result["other"]) == 1


def test_search_library_works_limit(user):
    for i in range(20):
        BookFactory(title=f"Match other {i:03d}")

    result = search_library_works(user, "Match", limit=5)

    assert len(result["other"]) <= 5
