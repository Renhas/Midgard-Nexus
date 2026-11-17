"""Tests for apps.vor_archives.artworks.services.queries."""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services.queries import (
    search_library_works,
    search_works,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    FilmFactory,
    GameFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

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
