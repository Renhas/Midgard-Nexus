"""Tests for CRUD from apps.vor_archives.artworks.services.collections."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    create_collection,
    delete_collection,
    get_user_collection,
    rename_collection,
)
from apps.vor_archives.artworks.services.collections import (
    next_collection_item_order,
    next_collection_order,
)
from apps.vor_archives.models import Collection
from apps.vor_archives.tests.factories import (
    CollectionFactory,
    CollectionItemFactory,
)

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
