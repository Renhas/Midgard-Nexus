"""Tests for Tree actions from apps.vor_archives.artworks.services.collections."""

import pytest
from django.core.exceptions import ValidationError

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    collection_tree_payload,
    get_user_collection_trees,
    move_collection,
)
from apps.vor_archives.tests.factories import CollectionFactory

pytestmark = pytest.mark.django_db


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
