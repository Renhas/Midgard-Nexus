"""Tests for apps.vor_archives.attributes.views.forms."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.models import BookGenre, FilmGenre, Platform, Tag
from apps.vor_archives.tests.factories import (
    BookGenreFactory,
    FilmGenreFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


def _form_urls():
    tag = TagFactory()
    genre = BookGenreFactory()
    return [
        reverse("vor_archives:attributes:new", args=["tags"]),
        reverse("vor_archives:attributes:new", args=["genres"]),
        reverse("vor_archives:attributes:edit", args=["tags", tag.pk]),
        reverse("vor_archives:attributes:genre_edit", args=["book", genre.pk]),
    ]


# ─── Доступ (login_required и require_staff) ────────────────────────────────


def test_form_views_require_login(client):
    for url in _form_urls():
        assert client.get(url).status_code == 302, url
        assert client.post(url).status_code == 302, url


def test_form_views_forbid_non_staff(client_logged_in):
    for url in _form_urls():
        assert client_logged_in.get(url).status_code == 403, url
        assert client_logged_in.post(url).status_code == 403, url


# ─── attr_new (простые атрибуты) ────────────────────────────────────────────


def test_attr_new_simple_get_and_post(staff_client):
    url = reverse("vor_archives:attributes:new", args=["platforms"])

    get_resp = staff_client.get(url)
    assert get_resp.status_code == 200
    assert get_resp.context["is_create"] is True
    assert get_resp.context["has_text"] is False

    # Невалидный POST
    bad_resp = staff_client.post(url, {"name": ""})
    assert bad_resp.status_code == 200
    assert bad_resp.context["form"].errors
    assert "HX-Trigger" not in bad_resp.headers
    assert Platform.objects.count() == 0

    # Валидный POST
    ok_resp = staff_client.post(url, {"name": "Steam Deck"})
    assert ok_resp.status_code == 200
    assert json.loads(ok_resp["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:attr-saved": {
            "isCreate": True,
            "oldName": "",
            "name": "Steam Deck",
            "changedFields": [],
        },
    }
    created = Platform.objects.get(name="Steam Deck")
    assert ok_resp.context["item"]["pk"] == created.pk


def test_attr_new_unknown_kind_404(staff_client):
    url = reverse("vor_archives:attributes:new", args=["unknown"])
    assert staff_client.get(url).status_code == 404
    assert staff_client.post(url, {"name": "Test"}).status_code == 404


# ─── attr_new (жанры) ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "query_params,expected_type,expected_label",
    [
        pytest.param({}, "book", "Книги", id="default-book"),
        pytest.param({"type": "film"}, "film", "Фильмы", id="explicit-film"),
        pytest.param({"type": "invalid"}, "book", "Книги", id="invalid-falls-back"),
    ],
)
def test_attr_new_genre_get_initial_type(
    staff_client, query_params, expected_type, expected_label
):
    response = staff_client.get(
        reverse("vor_archives:attributes:new", args=["genres"]),
        query_params,
    )
    assert response.status_code == 200
    assert response.context["form"].initial["type_key"] == expected_type
    assert response.context["type_label"] == expected_label


def test_attr_new_genre_post_valid_and_invalid(staff_client):
    url = reverse("vor_archives:attributes:new", args=["genres"])

    bad_resp = staff_client.post(url, {"type_key": "film", "name": "   "})
    assert bad_resp.status_code == 200
    assert bad_resp.context["form"].errors
    assert "HX-Trigger" not in bad_resp.headers
    assert FilmGenre.objects.count() == 0

    ok_resp = staff_client.post(
        url,
        {"type_key": "film", "name": "Noir", "description": "Classic noir"},
    )
    print(ok_resp["HX-Trigger"])
    assert ok_resp.status_code == 200
    assert json.loads(ok_resp["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:attr-saved": {
            "isCreate": True,
            "oldName": "",
            "name": "Noir",
            "changedFields": ["Описание"],
        },
    }
    created = FilmGenre.objects.get(name="Noir")
    assert created.description == "Classic noir"
    assert ok_resp.context["item"]["key"] == f"film:{created.pk}"


# ─── attr_edit ──────────────────────────────────────────────────────────────


def test_attr_edit_get_and_post(staff_client):
    tag = TagFactory(name="OldTag", description="Old")
    url = reverse("vor_archives:attributes:edit", args=["tags", tag.pk])

    get_resp = staff_client.get(url)
    assert get_resp.status_code == 200
    assert get_resp.context["is_create"] is False
    assert get_resp.context["pk"] == tag.pk

    # Конфликт уникальности
    TagFactory(name="Taken")
    bad_resp = staff_client.post(url, {"name": "TAKEN", "text": "New"})
    assert bad_resp.status_code == 200
    assert bad_resp.context["form"].errors
    assert "HX-Trigger" not in bad_resp.headers

    # Валидное обновление
    ok_resp = staff_client.post(url, {"name": "NewTag", "text": "Updated"})
    assert ok_resp.status_code == 200
    assert json.loads(ok_resp["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:attr-saved": {
            "isCreate": False,
            "oldName": "OldTag",
            "name": "NewTag",
            "changedFields": ["Описание"],
        },
    }
    tag.refresh_from_db()
    assert tag.name == "NewTag"
    assert tag.description == "Updated"


def test_attr_edit_edge_cases_404(staff_client):
    assert (
        staff_client.get(
            reverse("vor_archives:attributes:edit", args=["genres", 1])
        ).status_code
        == 404
    )
    assert (
        staff_client.get(
            reverse("vor_archives:attributes:edit", args=["unknown", 1])
        ).status_code
        == 404
    )
    assert (
        staff_client.get(
            reverse("vor_archives:attributes:edit", args=["tags", 999999])
        ).status_code
        == 404
    )


# ─── genre_edit ─────────────────────────────────────────────────────────────


def test_genre_edit_get_post_and_locked_type(staff_client):
    genre = BookGenreFactory(name="OldGenre", description="Old")
    url = reverse("vor_archives:attributes:genre_edit", args=["book", genre.pk])

    get_resp = staff_client.get(url)
    assert get_resp.status_code == 200
    assert get_resp.context["lock_type"] is True
    assert get_resp.context["type_label"] == "Книги"

    # Невалидный POST
    bad_resp = staff_client.post(url, {"name": ""})
    assert bad_resp.status_code == 200
    assert bad_resp.context["form"].errors
    assert "HX-Trigger" not in bad_resp.headers

    # Валидный POST с попыткой подменить type_key на film
    ok_resp = staff_client.post(
        url,
        {"type_key": "film", "name": "NewGenre", "description": "Updated"},
    )
    assert ok_resp.status_code == 200
    assert json.loads(ok_resp["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:attr-saved": {
            "isCreate": False,
            "oldName": "OldGenre",
            "name": "NewGenre",
            "changedFields": ["Описание"],
        },
    }
    genre.refresh_from_db()
    assert genre.name == "NewGenre"
    assert genre.description == "Updated"
    assert BookGenre.objects.filter(pk=genre.pk).exists()
    assert FilmGenre.objects.count() == 0


def test_genre_edit_edge_cases_400_and_404(staff_client):
    assert (
        staff_client.get(
            reverse("vor_archives:attributes:genre_edit", args=["invalid", 1])
        ).status_code
        == 400
    )
    assert (
        staff_client.get(
            reverse("vor_archives:attributes:genre_edit", args=["book", 999999])
        ).status_code
        == 404
    )
