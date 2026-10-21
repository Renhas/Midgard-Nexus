"""Tests for apps.vor_archives.artworks.services.collections."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    add_user_work_to_collection,
    collection_tree_payload,
    create_collection,
    delete_collection,
    get_user_collection,
    get_user_collection_trees,
    list_collection_segments,
    move_collection,
    remove_user_work_from_collection,
    rename_collection,
    reorder_collection_items,
    user_work_collection_ids,
)
from apps.vor_archives.artworks.services.collections import (
    next_collection_item_order,
    next_collection_order,
)
from apps.vor_archives.models import Collection, CollectionItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    UserWorkFactory,
)
from ...conftest import ALL_STATUSES

pytestmark = pytest.mark.django_db

# ─── get_user_collection ────────────────────────────────────────────────────


def test_get_user_collection_returns_own(user):
    coll = CollectionFactory(user=user)

    assert get_user_collection(user, coll.pk) == coll


def test_get_user_collection_foreign_raises_404(user):
    other = UserFactory()
    coll = CollectionFactory(user=other)

    with pytest.raises(Http404):
        get_user_collection(user, coll.pk)


def test_get_user_collection_missing_raises_404(user):
    with pytest.raises(Http404):
        get_user_collection(user, 999999)


# ─── get_user_collection_trees ──────────────────────────────────────────────


def test_get_user_collection_trees_returns_roots(user):
    root = CollectionFactory(user=user)
    CollectionFactory(user=user, parent=root)

    trees = get_user_collection_trees(user)

    assert len(trees) == 1
    assert trees[0].pk == root.pk


def test_get_user_collection_trees_ignores_other_users(user):
    other = UserFactory()
    CollectionFactory(user=other)

    assert list(get_user_collection_trees(user)) == []


# ─── next_collection_order / next_collection_item_order ─────────────────────


def test_next_collection_order_empty_root(user):
    assert next_collection_order(user) == 1


def test_next_collection_order_with_existing_root(user):
    CollectionFactory(user=user, order=5)

    assert next_collection_order(user) == 6


def test_next_collection_order_scoped_to_parent(user):
    parent = CollectionFactory(user=user, order=5)
    CollectionFactory(user=user, parent=parent, order=3)

    assert next_collection_order(user, parent) == 4
    assert next_collection_order(user) == 6


def test_next_collection_item_order_empty(user):
    coll = CollectionFactory(user=user)

    assert next_collection_item_order(coll) == 1


def test_next_collection_item_order_with_items(user, book):
    coll = CollectionFactory(user=user)
    CollectionItemFactory(collection=coll, work=book, order=7)

    assert next_collection_item_order(coll) == 8


# ─── create_collection ──────────────────────────────────────────────────────


def test_create_collection_basic(user):
    coll = create_collection(user, "My List")

    assert coll.name == "My List"
    assert coll.user == user
    assert coll.parent is None


def test_create_collection_strips_name(user):
    coll = create_collection(user, "  My List  ")

    assert coll.name == "My List"


def test_create_collection_empty_name_raises(user):
    with pytest.raises(ValidationError):
        create_collection(user, "")


def test_create_collection_whitespace_name_raises(user):
    with pytest.raises(ValidationError):
        create_collection(user, "   ")


def test_create_collection_none_name_raises(user):
    with pytest.raises(ValidationError):
        create_collection(user, None)


def test_create_collection_under_parent(user):
    parent = CollectionFactory(user=user)

    child = create_collection(user, "Child", parent=parent)

    assert child.parent == parent


# ─── rename_collection ──────────────────────────────────────────────────────


def test_rename_collection(user):
    coll = CollectionFactory(user=user, name="Old")

    rename_collection(user, coll.pk, "New")

    coll.refresh_from_db()
    assert coll.name == "New"


def test_rename_collection_strips_name(user):
    coll = CollectionFactory(user=user)

    rename_collection(user, coll.pk, "  New  ")

    coll.refresh_from_db()
    assert coll.name == "New"


def test_rename_collection_empty_raises(user):
    coll = CollectionFactory(user=user)

    with pytest.raises(ValidationError):
        rename_collection(user, coll.pk, "")


def test_rename_collection_foreign_raises_404(user):
    other = UserFactory()
    coll = CollectionFactory(user=other)

    with pytest.raises(Http404):
        rename_collection(user, coll.pk, "New")


# ─── delete_collection ──────────────────────────────────────────────────────


def test_delete_collection(user):
    coll = CollectionFactory(user=user)

    delete_collection(user, coll.pk)

    assert not Collection.objects.filter(pk=coll.pk).exists()


def test_delete_collection_cascades_to_children(user):
    parent = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=parent)

    delete_collection(user, parent.pk)

    assert not Collection.objects.filter(pk=child.pk).exists()


def test_delete_collection_foreign_raises_404(user):
    other = UserFactory()
    coll = CollectionFactory(user=other)

    with pytest.raises(Http404):
        delete_collection(user, coll.pk)


# ─── move_collection ────────────────────────────────────────────────────────


def test_move_collection_to_self_raises(user):
    coll = CollectionFactory(user=user)

    with pytest.raises(ValidationError):
        move_collection(user, coll.pk, coll.pk, [])


def test_move_collection_to_descendant_raises(user):
    parent = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=parent)

    with pytest.raises(ValidationError):
        move_collection(user, parent.pk, child.pk, [])


def test_move_collection_reparents(user):
    root_a = CollectionFactory(user=user)
    root_b = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root_a)

    move_collection(user, child.pk, root_b.pk, [child.pk])

    child.refresh_from_db()
    assert child.parent_id == root_b.pk


def test_move_collection_to_root(user):
    root = CollectionFactory(user=user)
    other_root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=other_root)

    move_collection(user, child.pk, None, [child.pk, root.pk])

    child.refresh_from_db()
    assert child.parent_id is None


def test_move_collection_reorders_siblings(user):
    root = CollectionFactory(user=user)
    a = CollectionFactory(user=user, parent=root, order=0)
    b = CollectionFactory(user=user, parent=root, order=1)
    c = CollectionFactory(user=user, parent=root, order=2)

    move_collection(user, a.pk, root.pk, [c.pk, a.pk, b.pk])

    a.refresh_from_db()
    b.refresh_from_db()
    c.refresh_from_db()
    assert (c.order, a.order, b.order) == (0, 1, 2)


def test_move_collection_appends_unspecified_siblings(user):
    root = CollectionFactory(user=user)
    a = CollectionFactory(user=user, parent=root, order=0)
    b = CollectionFactory(user=user, parent=root, order=1)
    c = CollectionFactory(user=user, parent=root, order=2)

    move_collection(user, a.pk, root.pk, [c.pk])

    a.refresh_from_db()
    b.refresh_from_db()
    c.refresh_from_db()
    assert (c.order, a.order, b.order) == (0, 1, 2)


def test_move_collection_ignores_invalid_sibling_ids(user):
    root = CollectionFactory(user=user)
    a = CollectionFactory(user=user, parent=root, order=0)

    move_collection(user, a.pk, root.pk, ["not-an-int", None, a.pk])

    a.refresh_from_db()
    assert a.order == 0


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


# ─── collection_tree_payload ────────────────────────────────────────────────


def test_collection_tree_payload_structure(user):
    root = CollectionFactory(user=user, name="Root")
    child = CollectionFactory(user=user, parent=root, name="Child")

    payload = collection_tree_payload(user)

    assert len(payload) == 1
    node = payload[0]
    assert node["id"] == root.pk
    assert node["name"] == "Root"
    assert node["in_collection"] is False
    assert len(node["children"]) == 1
    assert node["children"][0]["id"] == child.pk


def test_collection_tree_payload_marks_membership(user):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)

    payload = collection_tree_payload(user, member_ids=[child.pk])

    assert payload[0]["in_collection"] is False
    assert payload[0]["children"][0]["in_collection"] is True


def test_collection_tree_payload_ignores_other_users(user):
    other = UserFactory()
    CollectionFactory(user=other)

    assert collection_tree_payload(user) == []


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
