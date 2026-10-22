"""Tests for apps.vor_archives.artworks.views.collections."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.models import Collection, CollectionItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


def _trigger(response):
    return json.loads(response["HX-Trigger"])


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


# ─── collection_new ─────────────────────────────────────────────────────────


def test_collection_new_requires_login(client):
    response = client.get(reverse("vor_archives:collections:new"))
    assert response.status_code == 302


def test_collection_new_get_form(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:collections:new"))
    assert response.status_code == 200
    assert response.context["title"] == "Новая коллекция"
    assert response.context["submit_label"] == "Создать"
    assert response.context["action_url"] == reverse("vor_archives:collections:new")
    assert response.context["name"] == ""
    assert response.context["error"] == ""


def test_collection_new_post_valid_creates(client_logged_in, user):
    response = client_logged_in.post(
        reverse("vor_archives:collections:new"), {"name": "My List"}
    )
    assert response.status_code == 200
    trigger = _trigger(response)
    assert trigger["vor:reload-tree"] is True
    assert trigger["vor:close-modal"] is True
    assert trigger["collection-update"] is True
    assert Collection.objects.filter(user=user, name="My List").exists()


def test_collection_new_post_empty_rerenders_with_error(client_logged_in, user):
    response = client_logged_in.post(
        reverse("vor_archives:collections:new"), {"name": "   "}
    )
    assert response.status_code == 200
    assert response.context["error"] != ""
    assert not Collection.objects.filter(user=user).exists()


# ─── collection_edit ────────────────────────────────────────────────────────


def test_collection_edit_requires_login(client, user):
    collection = CollectionFactory(user=user)
    response = client.get(
        reverse("vor_archives:collections:edit", args=[collection.pk])
    )
    assert response.status_code == 302


def test_collection_edit_own(client_logged_in, user):
    collection = CollectionFactory(user=user, name="Old")
    response = client_logged_in.get(
        reverse("vor_archives:collections:edit", args=[collection.pk])
    )
    assert response.status_code == 200
    assert response.context["name"] == "Old"
    assert response.context["title"] == "Переименовать коллекцию"


def test_collection_edit_foreign_404(client_logged_in):
    other = UserFactory()
    collection = CollectionFactory(user=other)
    response = client_logged_in.get(
        reverse("vor_archives:collections:edit", args=[collection.pk])
    )
    assert response.status_code == 404


# ─── collection_update ──────────────────────────────────────────────────────


def test_collection_update_requires_login(client, user):
    collection = CollectionFactory(user=user)
    response = client.post(
        reverse("vor_archives:collections:update", args=[collection.pk]),
        {"name": "New"},
    )
    assert response.status_code == 302


def test_collection_update_post_valid(client_logged_in, user):
    collection = CollectionFactory(user=user, name="Old")
    response = client_logged_in.post(
        reverse("vor_archives:collections:update", args=[collection.pk]),
        {"name": "New"},
    )
    assert response.status_code == 200
    trigger = _trigger(response)
    assert trigger["vor:collection-renamed"] == {"id": collection.pk, "name": "New"}
    collection.refresh_from_db()
    assert collection.name == "New"


def test_collection_update_post_empty_rerenders(client_logged_in, user):
    collection = CollectionFactory(user=user, name="Old")
    response = client_logged_in.post(
        reverse("vor_archives:collections:update", args=[collection.pk]),
        {"name": ""},
    )
    assert response.status_code == 200
    assert response.context["error"] != ""
    collection.refresh_from_db()
    assert collection.name == "Old"


def test_collection_update_get_405(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.get(
        reverse("vor_archives:collections:update", args=[collection.pk])
    )
    assert response.status_code == 405


# ─── collection_delete_preview ──────────────────────────────────────────────


def test_collection_delete_preview_requires_login(client, user):
    collection = CollectionFactory(user=user)
    response = client.get(
        reverse("vor_archives:collections:delete_preview", args=[collection.pk])
    )
    assert response.status_code == 302


def test_collection_delete_preview_own(client_logged_in, user):
    collection = CollectionFactory(user=user)
    CollectionFactory(user=user, parent=collection)
    response = client_logged_in.get(
        reverse("vor_archives:collections:delete_preview", args=[collection.pk])
    )
    assert response.status_code == 200
    assert response.context["collection"] == collection
    assert response.context["child_count"] == 1


def test_collection_delete_preview_foreign_404(client_logged_in):
    other = UserFactory()
    collection = CollectionFactory(user=other)
    response = client_logged_in.get(
        reverse("vor_archives:collections:delete_preview", args=[collection.pk])
    )
    assert response.status_code == 404


# ─── collection_delete ──────────────────────────────────────────────────────


def test_collection_delete_requires_login(client, user):
    collection = CollectionFactory(user=user)
    response = client.post(
        reverse("vor_archives:collections:delete", args=[collection.pk])
    )
    assert response.status_code == 302


def test_collection_delete_post(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.post(
        reverse("vor_archives:collections:delete", args=[collection.pk])
    )
    assert response.status_code == 200
    trigger = _trigger(response)
    assert trigger["vor:collection-deleted"] == collection.pk
    assert not Collection.objects.filter(pk=collection.pk).exists()


def test_collection_delete_get_405(client_logged_in, user):
    collection = CollectionFactory(user=user)
    response = client_logged_in.get(
        reverse("vor_archives:collections:delete", args=[collection.pk])
    )
    assert response.status_code == 405


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
