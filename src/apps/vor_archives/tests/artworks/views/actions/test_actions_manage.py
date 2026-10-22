"""Tests for apps.vor_archives.artworks.views.actions."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import (
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


# ─── artwork_reorder ────────────────────────────────────────────────────────


def test_reorder_requires_login(client):
    response = client.post(reverse("vor_archives:artworks:reorder"))
    assert response.status_code == 302


def test_reorder_get_405(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:reorder"))
    assert response.status_code == 405


def test_reorder_ok(client_logged_in, user, book, movie):
    uw1 = UserWorkFactory(user=user, work=book)
    uw2 = UserWorkFactory(user=user, work=movie)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:reorder"),
        {"ids": [str(uw2.pk), str(uw1.pk)]},
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}
    uw1.refresh_from_db()
    uw2.refresh_from_db()
    assert uw2.order_position == 0
    assert uw1.order_position == 1


# ─── artwork_delete_preview ─────────────────────────────────────────────────


def test_delete_preview_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 302


def test_delete_preview_get_only(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 405


def test_delete_preview_empty(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 200
    assert response.context["count"] == 0
    assert response.context["ids"] == []
    assert response.context["orphan_titles"] == []


def test_delete_preview_own_uw(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(uw.pk)]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 1
    assert response.context["orphan_titles"] == [book.title]


def test_delete_preview_foreign_uw_ignored(client_logged_in, book):
    other = UserFactory()
    foreign = UserWorkFactory(user=other, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(foreign.pk)]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 0


def test_delete_preview_shared_work_not_orphan(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    other = UserFactory()
    UserWorkFactory(user=other, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(uw.pk)]},
    )
    assert response.status_code == 200
    assert response.context["orphan_titles"] == []
