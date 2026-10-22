"""Tests for apps.vor_archives.artworks.views.collections."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.models import CollectionItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db

# ─── collection_items ───────────────────────────────────────────────────────


def test_collection_items_requires_login(client, user, book):
    collection = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    response = client.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(uw.pk)},
    )
    assert response.status_code == 302


def test_collection_items_foreign_collection_404(client_logged_in, user, book):
    other = UserFactory()
    foreign = CollectionFactory(user=other)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[foreign.pk]),
        {"uw_id": str(uw.pk)},
    )
    assert response.status_code == 404


def test_collection_items_missing_uw_id_400(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]), {}
    )
    assert response.status_code == 400


def test_collection_items_foreign_uw_404(client_logged_in, user):
    other = UserFactory()
    collection = CollectionFactory(user=user)
    foreign_uw = UserWorkFactory(user=other, work=BookFactory())
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(foreign_uw.pk)},
    )
    assert response.status_code == 404


def test_collection_items_add(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(uw.pk), "action": "add"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["changed"] is True
    assert payload["in_collection"] is True
    assert payload["collection_id"] == collection.pk
    assert CollectionItem.objects.filter(
        collection=collection, work_object_id=book.pk
    ).exists()


def test_collection_items_add_duplicate_changed_false(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    CollectionItemFactory(collection=collection, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(uw.pk), "action": "add"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["changed"] is False
    assert payload["in_collection"] is True


def test_collection_items_remove(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    CollectionItemFactory(collection=collection, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(uw.pk), "action": "remove"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["changed"] is True
    assert payload["in_collection"] is False
    assert not CollectionItem.objects.filter(
        collection=collection, work_object_id=book.pk
    ).exists()


def test_collection_items_remove_absent_changed_false(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items", args=[collection.pk]),
        {"uw_id": str(uw.pk), "action": "remove"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["changed"] is False
    assert payload["in_collection"] is False


def test_collection_items_get_405(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.get(
        reverse("vor_archives:collections:items", args=[collection.pk])
    )
    assert response.status_code == 405


# ─── collection_items_reorder ───────────────────────────────────────────────


def test_collection_items_reorder_requires_login(client, user):
    collection = CollectionFactory(user=user)
    response = client.post(
        reverse("vor_archives:collections:items_reorder", args=[collection.pk])
    )
    assert response.status_code == 302


def test_collection_items_reorder_foreign_404(client_logged_in):
    from apps.users.tests.factories import UserFactory

    other = UserFactory()
    foreign = CollectionFactory(user=other)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items_reorder", args=[foreign.pk])
    )
    assert response.status_code == 404


def test_collection_items_reorder_ok(client_logged_in, user, book, movie):
    collection = CollectionFactory(user=user)
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)
    CollectionItemFactory(collection=collection, work=book, order=0)
    CollectionItemFactory(collection=collection, work=movie, order=1)
    response = client_logged_in.post(
        reverse("vor_archives:collections:items_reorder", args=[collection.pk]),
        {"ids": [str(uw_movie.pk), str(uw_book.pk)]},
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}
