"""Tests for collection CRUD views: new, edit, update, delete preview, delete."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.models import Collection
from apps.vor_archives.tests.factories import (
    CollectionFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


def _trigger(response):
    return json.loads(response["HX-Trigger"])


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
