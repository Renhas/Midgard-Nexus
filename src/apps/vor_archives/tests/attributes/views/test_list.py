"""Tests for apps.vor_archives.attributes.views.list."""

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import (
    BookGenreFactory,
    FilmGenreFactory,
    GameGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── Авторизация и HTTP-методы ──────────────────────────────────────────────


def test_list_views_require_login(client):
    tag = TagFactory()
    genre = BookGenreFactory()
    urls = [
        reverse("vor_archives:attributes:list", args=["tags"]),
        reverse("vor_archives:attributes:empty", args=["tags"]),
        reverse("vor_archives:attributes:detail", args=["tags", tag.pk]),
        reverse("vor_archives:attributes:genre_detail", args=["book", genre.pk]),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 302, url


def test_list_views_reject_post(client_logged_in):
    tag = TagFactory()
    genre = BookGenreFactory()
    urls = [
        reverse("vor_archives:attributes:list", args=["tags"]),
        reverse("vor_archives:attributes:empty", args=["tags"]),
        reverse("vor_archives:attributes:detail", args=["tags", tag.pk]),
        reverse("vor_archives:attributes:genre_detail", args=["book", genre.pk]),
    ]
    for url in urls:
        response = client_logged_in.post(url)
        assert response.status_code == 405, url


# ─── attr_list & attr_empty ─────────────────────────────────────────────────


def test_attr_list_simple_and_search_filter(client_logged_in):
    TagFactory(name="Cyberpunk")
    TagFactory(name="Steampunk")

    response = client_logged_in.get(
        reverse("vor_archives:attributes:list", args=["tags"]),
        {"q": "cyber"},
    )
    assert response.status_code == 200
    assert response.context["total_count"] == 2
    assert [i["name"] for i in response.context["items"]] == ["Cyberpunk"]
    assert "Cyberpunk" in response.content.decode()
    assert "Steampunk" not in response.content.decode()


def test_attr_list_genres(client_logged_in):
    BookGenreFactory(name="Fantasy")
    FilmGenreFactory(name="Noir")

    response = client_logged_in.get(
        reverse("vor_archives:attributes:list", args=["genres"])
    )
    assert response.status_code == 200
    assert response.context["total_count"] == 2
    assert response.context["has_items"] is True
    content = response.content.decode()
    assert "Fantasy" in content
    assert "Noir" in content


def test_attr_list_and_empty_unknown_kind_404(client_logged_in):
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:list", args=["unknown"])
        ).status_code
        == 404
    )
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:empty", args=["unknown"])
        ).status_code
        == 404
    )


def test_attr_empty_renders_prompt(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:attributes:empty", args=["persons"])
    )
    assert response.status_code == 200
    assert response.context["empty_prompt"] in response.content.decode()


# ─── attr_detail & genre_detail ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "kind,factory_fn",
    [
        pytest.param(
            "tags", lambda: TagFactory(name="TagOne", description="Desc"), id="tags"
        ),
        pytest.param(
            "persons", lambda: PersonFactory(name="AuthorOne", bio="Bio"), id="persons"
        ),
        pytest.param("platforms", lambda: PlatformFactory(name="PC"), id="platforms"),
    ],
)
def test_attr_detail_ok(client_logged_in, kind, factory_fn):
    obj = factory_fn()
    response = client_logged_in.get(
        reverse("vor_archives:attributes:detail", args=[kind, obj.pk])
    )
    assert response.status_code == 200
    assert response.context["item"]["pk"] == obj.pk
    assert obj.name in response.content.decode()


def test_attr_detail_edge_cases(client_logged_in):
    # kind='genres' требует type_key -> 400
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:detail", args=["genres", 1])
        ).status_code
        == 400
    )
    # Неизвестный kind -> 404
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:detail", args=["unknown", 1])
        ).status_code
        == 404
    )
    # Несуществующий pk -> 404
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:detail", args=["tags", 999999])
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    "type_key,factory_fn",
    [
        pytest.param("book", lambda: BookGenreFactory(name="BookG"), id="book"),
        pytest.param("film", lambda: FilmGenreFactory(name="FilmG"), id="film"),
        pytest.param("game", lambda: GameGenreFactory(name="GameG"), id="game"),
    ],
)
def test_genre_detail_ok(client_logged_in, type_key, factory_fn):
    genre = factory_fn()
    response = client_logged_in.get(
        reverse("vor_archives:attributes:genre_detail", args=[type_key, genre.pk])
    )
    assert response.status_code == 200
    assert response.context["item"]["pk"] == genre.pk
    assert genre.name in response.content.decode()


def test_genre_detail_edge_cases(client_logged_in):
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:genre_detail", args=["invalid", 1])
        ).status_code
        == 400
    )
    assert (
        client_logged_in.get(
            reverse("vor_archives:attributes:genre_detail", args=["book", 999999])
        ).status_code
        == 404
    )
