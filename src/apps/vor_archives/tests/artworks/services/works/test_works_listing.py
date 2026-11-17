"""Tests for apps.vor_archives.artworks.services.works - listing.

Covers list_user_works: basic listing with type/status filters and sorting.
Collection-scoped listing lives in tests/artworks/services/collections/.
"""

import pytest

from apps.vor_archives.artworks.services import list_user_works
from apps.vor_archives.tests.factories import (
    BookFactory,
    FilmFactory,
    UserWorkFactory,
)
from apps.vor_archives.tests.conftest import ALL_STATUSES

pytestmark = pytest.mark.django_db


# ─── list_user_works ─────────────────────────────────────────────────────────


def test_list_user_works_empty_without_types(user, book):
    UserWorkFactory(user=user, work=book)

    assert list_user_works(user, {}) == []


def test_list_user_works_basic(user, book):
    uw = UserWorkFactory(user=user, work=book)

    result = list_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert result == [uw]


def test_list_user_works_sorted_by_title(user):
    book = BookFactory(title="Zeta")
    film = FilmFactory(title="Alpha")
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=film)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "sort": "title",
            "sort_asc": True,
        },
    )

    assert [uw.work.title for uw in result] == ["Alpha", "Zeta"]
