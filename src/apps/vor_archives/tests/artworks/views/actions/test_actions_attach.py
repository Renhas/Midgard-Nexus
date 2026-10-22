"""Tests for apps.vor_archives.artworks.views.actions."""

import json
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import UserWorkFactory


pytestmark = pytest.mark.django_db


# ─── artwork_attach ─────────────────────────────────────────────────────────


def test_attach_missing_fields_400(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:attach"), {})
    assert response.status_code == 400


def test_attach_missing_work_id_400(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"), {"work_type": "book"}
    )
    assert response.status_code == 400


def test_attach_already_owned_json_400(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False
    assert payload["error"] == "already"


def test_attach_already_owned_html_renders_preview(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
    )
    assert response.status_code == 200
    assert response.context["already"] is True
    assert response.context["work"] == book


def test_attach_invalid_status_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "status": "bogus"},
    )
    assert response.status_code == 400


def test_attach_invalid_rating_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "rating": "11"},
    )
    assert response.status_code == 400


def test_attach_rating_zero_treated_as_none(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "rating": "0",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    uw = UserWork.objects.get(user=user)
    assert uw.rating is None


def test_attach_invalid_progress_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "progress": "abc"},
    )
    assert response.status_code == 400


def test_attach_negative_progress_clamped(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "progress": "-5",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    uw = UserWork.objects.get(user=user)
    assert uw.progress == Decimal("0")


def test_attach_valid_json_creates_userwork(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "status": UserWorkStatusChoices.IN_PROGRESS,
            "rating": "8",
            "progress": "42.5",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}
    uw = UserWork.objects.get(user=user, work_object_id=book.pk)
    assert uw.status == UserWorkStatusChoices.IN_PROGRESS
    assert uw.rating == 8
    assert uw.progress == Decimal("42.5")


def test_attach_valid_html_returns_trigger(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
    )
    assert response.status_code == 200
    trigger = json.loads(response["HX-Trigger"])
    assert trigger.get("vor:reload-list") is True
    assert trigger.get("vor:close-overlay") is True


# ─── artwork_preview ────────────────────────────────────────────────────────


def test_preview_requires_login(client, book):
    response = client.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 302


def test_preview_missing_work_id_400(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:preview"))
    assert response.status_code == 400


def test_preview_default_type_book(client_logged_in, book):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 200
    assert response.context["work_type"] == "book"
    assert response.context["work"] == book


def test_preview_explicit_type(client_logged_in, movie):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"),
        {"type": "film", "work_id": movie.pk},
    )
    assert response.status_code == 200
    assert response.context["work_type"] == "film"


def test_preview_already_owned(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 200
    assert response.context["already"] is True
