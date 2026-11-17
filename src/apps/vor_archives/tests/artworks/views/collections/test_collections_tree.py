"""Tests for collection tree views: artwork_collections, collection_tree, collection_reorder."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


# ─── artwork_collections ────────────────────────────────────────────────────


def test_artwork_collections_requires_login(client, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client.get(reverse("vor_archives:artworks:collections", args=[uw.pk]))
    assert response.status_code == 302


def test_artwork_collections_get_only(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:collections", args=[uw.pk])
    )
    assert response.status_code == 405


def test_artwork_collections_foreign_uw_404(client_logged_in):
    other = UserFactory()
    uw = UserWorkFactory(user=other, work=BookFactory())
    response = client_logged_in.get(
        reverse("vor_archives:artworks:collections", args=[uw.pk])
    )
    assert response.status_code == 404


def test_artwork_collections_returns_tree(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    collection = CollectionFactory(user=user, name="Root")
    CollectionItemFactory(collection=collection, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:collections", args=[uw.pk])
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert len(payload["tree"]) == 1
    assert payload["tree"][0]["in_collection"] is True


# ─── collection_tree ────────────────────────────────────────────────────────


def test_collection_tree_requires_login(client):
    response = client.get(reverse("vor_archives:collections:tree"))
    assert response.status_code == 302


def test_collection_tree_renders(client_logged_in, user):
    CollectionFactory(user=user, name="Root")
    response = client_logged_in.get(reverse("vor_archives:collections:tree"))
    assert response.status_code == 200
    assert len(list(response.context["collections"])) == 1


# ─── collection_reorder ─────────────────────────────────────────────────────


def test_collection_reorder_requires_login(client):
    response = client.post(reverse("vor_archives:collections:reorder"))
    assert response.status_code == 302


def test_collection_reorder_missing_id_400(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:collections:reorder"), {})
    assert response.status_code == 400


def test_collection_reorder_valid(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.post(
        reverse("vor_archives:collections:reorder"),
        {"id": str(collection.pk), "sibling_ids": [str(collection.pk)]},
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}


def test_collection_reorder_validation_error_400(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.post(
        reverse("vor_archives:collections:reorder"),
        {"id": str(collection.pk), "parent_id": str(collection.pk)},
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False
    assert payload["error"]


def test_collection_reorder_foreign_id_400(client_logged_in):
    other = UserFactory()
    foreign = CollectionFactory(user=other)
    response = client_logged_in.post(
        reverse("vor_archives:collections:reorder"), {"id": str(foreign.pk)}
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False


def test_collection_reorder_get_405(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:collections:reorder"))
    assert response.status_code == 405
