"""Tests for CollectionItems actions from apps.vor_archives.artworks.services.collections."""

from unittest import mock

from django.db import IntegrityError
import pytest
from django.core.exceptions import ValidationError

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    add_user_work_to_collection,
    list_collection_segments,
    remove_user_work_from_collection,
    reorder_collection_items,
    user_work_collection_ids,
)
from apps.vor_archives.models import CollectionItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    FilmFactory,
    UserWorkFactory,
)
from apps.vor_archives.tests.conftest import ALL_STATUSES

pytestmark = pytest.mark.django_db


# ─── list_collection_segments ───────────────────────────────────────────────


def test_list_collection_segments_empty(user):
    coll = CollectionFactory(user=user)

    result = list_collection_segments(user, coll, {"types": ["book"]})

    assert result == {"direct": [], "nested": []}


def test_list_collection_segments_direct(user, book):
    coll = CollectionFactory(user=user)
    CollectionItemFactory(collection=coll, work=book)
    UserWorkFactory(user=user, work=book)

    result = list_collection_segments(
        user,
        coll,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert len(result["direct"]) == 1
    assert result["direct"][0].work_object_id == book.pk
    assert result["nested"] == []


def test_list_collection_segments_nested(user, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    CollectionItemFactory(collection=child, work=movie)
    UserWorkFactory(user=user, work=movie)

    result = list_collection_segments(
        user,
        root,
        {
            "types": ["film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert result["direct"] == []
    assert len(result["nested"]) == 1
    assert result["nested"][0]["collection"] == child
    assert len(result["nested"][0]["user_works"]) == 1


def test_list_collection_segments_skips_unowned(user, book):
    coll = CollectionFactory(user=user)
    CollectionItemFactory(collection=coll, work=book)
    # No UserWork for the user - should not appear

    result = list_collection_segments(user, coll, {"types": ["book"]})

    assert result["direct"] == []


def test_list_collection_segments_non_custom_sort(user):
    coll = CollectionFactory(user=user)
    film = FilmFactory(title="Alpha")
    book = BookFactory(title="Zeta")
    CollectionItemFactory(collection=coll, work=film, order=0)
    CollectionItemFactory(collection=coll, work=book, order=1)
    UserWorkFactory(user=user, work=film)
    UserWorkFactory(user=user, work=book)

    result = list_collection_segments(
        user,
        coll,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "sort": "title",
            "sort_asc": True,
        },
    )

    assert [uw.work.title for uw in result["direct"]] == ["Alpha", "Zeta"]


# ─── add_user_work_to_collection ────────────────────────────────────────────


def test_add_user_work_creates_item(user, book):
    coll = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)

    item, created = add_user_work_to_collection(user, coll, uw)

    assert created is True
    assert item.collection == coll
    assert item.work_object_id == book.pk


def test_add_user_work_is_idempotent(user, book):
    coll = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)

    item1, created1 = add_user_work_to_collection(user, coll, uw)
    item2, created2 = add_user_work_to_collection(user, coll, uw)

    assert created1 is True
    assert created2 is False
    assert item1.pk == item2.pk


def test_add_user_work_foreign_uw_raises(user, book):
    coll = CollectionFactory(user=user)
    other = UserFactory()
    foreign_uw = UserWorkFactory(user=other, work=book)

    with pytest.raises(ValidationError):
        add_user_work_to_collection(user, coll, foreign_uw)


def test_add_user_work_foreign_collection_raises(user, book):
    other = UserFactory()
    foreign_coll = CollectionFactory(user=other)
    uw = UserWorkFactory(user=user, work=book)

    with pytest.raises(ValidationError):
        add_user_work_to_collection(user, foreign_coll, uw)


@pytest.mark.django_db
def test_add_user_work_handles_integrity_error(user, book):
    coll = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    existing = CollectionItemFactory(collection=coll, work=book)

    with mock.patch.object(
        CollectionItem.objects,
        "get_or_create",
        side_effect=IntegrityError("simulated race"),
    ):
        item, created = add_user_work_to_collection(user, coll, uw)

    assert created is False
    assert item.pk == existing.pk


# ─── remove_user_work_from_collection ───────────────────────────────────────


def test_remove_user_work_returns_true_when_deleted(user, book):
    coll = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    add_user_work_to_collection(user, coll, uw)

    assert remove_user_work_from_collection(user, coll, uw) is True
    assert remove_user_work_from_collection(user, coll, uw) is False


def test_remove_user_work_foreign_raises(user, book):
    coll = CollectionFactory(user=user)
    other = UserFactory()
    foreign_uw = UserWorkFactory(user=other, work=book)

    with pytest.raises(ValidationError):
        remove_user_work_from_collection(user, coll, foreign_uw)


# ─── user_work_collection_ids ───────────────────────────────────────────────


def test_user_work_collection_ids(user, book):
    c1 = CollectionFactory(user=user)
    c2 = CollectionFactory(user=user)
    c3 = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    add_user_work_to_collection(user, c1, uw)
    add_user_work_to_collection(user, c2, uw)

    ids = user_work_collection_ids(user, uw)

    assert ids == {c1.pk, c2.pk}
    assert c3.pk not in ids


def test_user_work_collection_ids_ignores_other_users(user, book):
    other = UserFactory()
    foreign_coll = CollectionFactory(user=other)
    uw = UserWorkFactory(user=user, work=book)
    CollectionItemFactory(collection=foreign_coll, work=book)

    assert user_work_collection_ids(user, uw) == set()


# ─── reorder_collection_items ───────────────────────────────────────────────


def test_reorder_collection_items_full(user, book, movie, game):
    coll = CollectionFactory(user=user)
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)
    uw_game = UserWorkFactory(user=user, work=game)
    add_user_work_to_collection(user, coll, uw_book)
    add_user_work_to_collection(user, coll, uw_movie)
    add_user_work_to_collection(user, coll, uw_game)

    count = reorder_collection_items(user, coll, [uw_game.pk, uw_book.pk, uw_movie.pk])

    assert count == 3
    items = {
        item.work_object_id: item
        for item in CollectionItem.objects.filter(collection=coll)
    }
    assert items[game.pk].order == 0
    assert items[book.pk].order == 1
    assert items[movie.pk].order == 2


def test_reorder_collection_items_partial(user, book, movie, game):
    coll = CollectionFactory(user=user)
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)
    uw_game = UserWorkFactory(user=user, work=game)
    add_user_work_to_collection(user, coll, uw_book)
    add_user_work_to_collection(user, coll, uw_movie)
    add_user_work_to_collection(user, coll, uw_game)

    count = reorder_collection_items(user, coll, [uw_movie.pk, uw_book.pk])

    assert count == 2
    items = {
        item.work_object_id: item
        for item in CollectionItem.objects.filter(collection=coll)
    }
    assert items[movie.pk].order == 0
    assert items[book.pk].order == 1
    # game is left at its original order (3, since next_collection_item_order starts at 1)
    assert items[game.pk].order == 3


def test_reorder_collection_items_foreign_collection_raises(user):
    other = UserFactory()
    foreign_coll = CollectionFactory(user=other)

    with pytest.raises(ValidationError):
        reorder_collection_items(user, foreign_coll, [])


def test_reorder_collection_items_ignores_foreign_uw(user, book):
    coll = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    add_user_work_to_collection(user, coll, uw)
    other = UserFactory()
    foreign_uw = UserWorkFactory(user=other, work=BookFactory())

    count = reorder_collection_items(user, coll, [uw.pk, foreign_uw.pk])

    assert count == 1


def test_reorder_collection_items_ignores_items_not_in_collection(user, book, movie):
    coll = CollectionFactory(user=user)
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)
    add_user_work_to_collection(user, coll, uw_book)

    count = reorder_collection_items(user, coll, [uw_movie.pk, uw_book.pk])

    assert count == 1
