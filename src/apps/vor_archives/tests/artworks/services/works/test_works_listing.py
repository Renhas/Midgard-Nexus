"""Tests for apps.vor_archives.artworks.services.works - listing.

Covers list_user_works and collection_scope_keys, including type,
status, visibility and collection filters plus sort parameter passthrough.
"""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import list_user_works
from apps.vor_archives.artworks.services.utils import work_key
from apps.vor_archives.artworks.services.works import collection_scope_keys
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    FilmFactory,
    UserWorkFactory,
)
from apps.vor_archives.tests.conftest import ALL_STATUSES

pytestmark = pytest.mark.django_db

# ─── collection_scope_keys ───────────────────────────────────────────────────


def test_collection_scope_keys_direct_only(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    item_book = CollectionItemFactory(collection=root, work=book)
    CollectionItemFactory(collection=child, work=movie)

    keys = collection_scope_keys(root, include_descendants=False)

    assert keys == {work_key(item_book)}


def test_collection_scope_keys_with_descendants(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    item_book = CollectionItemFactory(collection=root, work=book)
    item_movie = CollectionItemFactory(collection=child, work=movie)

    keys = collection_scope_keys(root, include_descendants=True)

    assert keys == {work_key(item_book), work_key(item_movie)}


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


def test_list_user_works_unknown_collection_returns_empty(user, book):
    UserWorkFactory(user=user, work=book)

    result = list_user_works(user, {"types": ["book"], "collection_id": 999999})

    assert result == []


def test_list_user_works_foreign_collection_returns_empty(user, book):
    other = UserFactory()
    foreign_collection = CollectionFactory(user=other)
    UserWorkFactory(user=user, work=book)

    result = list_user_works(
        user, {"types": ["book"], "collection_id": foreign_collection.pk}
    )

    assert result == []


def test_list_user_works_collection_filter_excludes_outsiders(user, book, movie):
    collection = CollectionFactory(user=user)
    CollectionItemFactory(collection=collection, work=book)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "collection_id": collection.pk,
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == book.pk


def test_list_user_works_includes_collection_descendants(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    CollectionItemFactory(collection=child, work=movie)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "collection_id": root.pk,
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == movie.pk


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
