"""Tests for apps.vor_archives.attributes.views.delete."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.models import BookGenre, FilmGenre, Tag
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmFactory,
    FilmGenreFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── Доступ и HTTP-методы ───────────────────────────────────────────────────


def test_delete_views_require_login(client):
    preview_url = reverse("vor_archives:attributes:delete_preview", args=["tags"])
    delete_url = reverse("vor_archives:attributes:delete", args=["tags"])
    assert client.get(preview_url).status_code == 302
    assert client.post(delete_url).status_code == 302


def test_delete_views_forbid_non_staff(client_logged_in):
    preview_url = reverse("vor_archives:attributes:delete_preview", args=["tags"])
    delete_url = reverse("vor_archives:attributes:delete", args=["tags"])
    assert client_logged_in.get(preview_url).status_code == 403
    assert client_logged_in.post(delete_url).status_code == 403


def test_delete_views_enforce_http_methods(staff_client):
    preview_url = reverse("vor_archives:attributes:delete_preview", args=["tags"])
    delete_url = reverse("vor_archives:attributes:delete", args=["tags"])
    assert staff_client.post(preview_url).status_code == 405
    assert staff_client.get(delete_url).status_code == 405


# ─── attr_delete_preview ────────────────────────────────────────────────────


def test_attr_delete_preview_single_item_text_and_linked_count(staff_client):
    tag = TagFactory(name="Cyberpunk")
    b1 = BookFactory()
    b2 = BookFactory()
    b1.tags.add(tag)
    b2.tags.add(tag)

    response = staff_client.get(
        reverse("vor_archives:attributes:delete_preview", args=["tags"]),
        {"ids": [str(tag.pk)]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 1
    assert response.context["linked_count"] == 2
    assert response.context["delete_text"] == "Тег «Cyberpunk» будет удалён."
    assert response.context["delete_url"] == reverse(
        "vor_archives:attributes:delete", args=["tags"]
    )


def test_attr_delete_preview_multiple_genres_and_csv_ids(staff_client):
    bg = BookGenreFactory(name="Fantasy")
    fg = FilmGenreFactory(name="Drama")
    book = BookFactory()
    film = FilmFactory()
    book.genres.add(bg)
    film.genres.add(fg)

    response = staff_client.get(
        reverse("vor_archives:attributes:delete_preview", args=["genres"]),
        {"ids": [f"book:{bg.pk},film:{fg.pk}"]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 2
    assert response.context["linked_count"] == 2
    assert response.context["delete_text"] == "Выбранные жанры (2) будут удалены."


def test_attr_delete_preview_unknown_kind_404(staff_client):
    response = staff_client.get(
        reverse("vor_archives:attributes:delete_preview", args=["unknown"]),
        {"ids": ["1"]},
    )
    assert response.status_code == 404


# ─── attr_delete ────────────────────────────────────────────────────────────


def test_attr_delete_simple_deletes_and_triggers_refresh_and_modal_close(staff_client):
    t1 = TagFactory()
    t2 = TagFactory()
    untouched = TagFactory()

    response = staff_client.post(
        reverse("vor_archives:attributes:delete", args=["tags"]),
        {"ids": [str(t1.pk), str(t2.pk)]},
    )
    assert response.status_code == 200
    assert not Tag.objects.filter(pk__in=[t1.pk, t2.pk]).exists()
    assert Tag.objects.filter(pk=untouched.pk).exists()
    assert json.loads(response["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:close-attr-modal": True,
        "vor:attr-deleted": {"count": 2},
    }


def test_attr_delete_genres_across_types(staff_client):
    bg = BookGenreFactory()
    fg = FilmGenreFactory()

    response = staff_client.post(
        reverse("vor_archives:attributes:delete", args=["genres"]),
        {"ids": [f"book:{bg.pk},film:{fg.pk}"]},
    )
    assert response.status_code == 200
    assert not BookGenre.objects.filter(pk=bg.pk).exists()
    assert not FilmGenre.objects.filter(pk=fg.pk).exists()
    assert json.loads(response["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:close-attr-modal": True,
        "vor:attr-deleted": {"count": 2},
    }


def test_attr_delete_unknown_kind_404(staff_client):
    response = staff_client.post(
        reverse("vor_archives:attributes:delete", args=["unknown"]),
        {"ids": ["1"]},
    )
    assert response.status_code == 404
