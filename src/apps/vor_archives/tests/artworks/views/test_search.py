"""Tests for apps.vor_archives.artworks.views.search."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import (
    BookFactory,
    FilmFactory,
    UserWorkFactory,
)


pytestmark = pytest.mark.django_db


# ─── artwork_library_search ─────────────────────────────────────────────────


def test_library_search_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:library_search"))
    assert response.status_code == 302


def test_library_search_get_only(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:library_search"))
    assert response.status_code == 405


def test_library_search_empty_query(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:library_search"), {"q": ""}
    )
    assert response.status_code == 200
    assert response.context["owned"] == []
    assert response.context["other"] == []
    assert response.context["query"] == ""


def test_library_search_owned_has_detail_url(client_logged_in, user):
    book = BookFactory(title="Match owned")
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:library_search"), {"q": "Match"}
    )
    assert response.status_code == 200
    owned = response.context["owned"]
    assert len(owned) == 1
    assert owned[0]["uw_id"] == uw.pk
    assert owned[0]["detail_url"] == reverse(
        "vor_archives:artworks:detail", args=[uw.pk]
    )


def test_library_search_other_has_detail_url(client_logged_in):
    book = BookFactory(title="Match other")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:library_search"), {"q": "Match"}
    )
    other = response.context["other"]
    assert len(other) == 1
    assert other[0]["detail_url"] == reverse(
        "vor_archives:artworks:work", args=["book", book.pk]
    )


def test_library_search_query_stripped(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:library_search"), {"q": "  match  "}
    )
    assert response.context["query"] == "match"


# ─── artwork_search ─────────────────────────────────────────────────────────


def test_search_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:search"))
    assert response.status_code == 302


def test_search_empty_query(client_logged_in):
    BookFactory(title="Solo")
    response = client_logged_in.get(reverse("vor_archives:artworks:search"), {"q": ""})
    assert response.status_code == 200
    assert response.context["works"] == []
    assert response.context["already_owned"] is False


def test_search_finds_match(client_logged_in):
    book = BookFactory(title="Foundation")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:search"), {"q": "Found", "work_type": "book"}
    )
    assert response.status_code == 200
    assert len(response.context["works"]) == 1
    assert response.context["works"][0].pk == book.pk


def test_search_excludes_owned(client_logged_in, user):
    book = BookFactory(title="Owned Book")
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:search"),
        {"q": "Owned", "work_type": "book"},
    )
    assert response.context["works"] == []


def test_search_already_owned_exact_match(client_logged_in, user):
    book = BookFactory(title="Exact Title")
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:search"),
        {"q": "Exact Title", "work_type": "book"},
    )
    assert response.context["already_owned"] is True


def test_search_unknown_type_empty(client_logged_in):
    BookFactory(title="Foo")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:search"),
        {"q": "Foo", "work_type": "nope"},
    )
    assert response.status_code == 200
    assert response.context["works"] == []


def test_search_uses_type_alias(client_logged_in):
    movie = FilmFactory(title="Alias")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:search"), {"q": "Alias", "type": "film"}
    )
    assert response.status_code == 200
    assert response.context["work_type"] == "film"
    assert response.context["works"][0].pk == movie.pk


# ─── artwork_relation_search ────────────────────────────────────────────────


def test_relation_search_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:relation_search"))
    assert response.status_code == 302


def test_relation_search_empty(client_logged_in):
    BookFactory(title="Anything")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:relation_search"), {"q": ""}
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"results": []}


def test_relation_search_finds(client_logged_in):
    book = BookFactory(title="Foundation")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:relation_search"), {"q": "Found"}
    )
    payload = json.loads(response.content)
    assert any(
        r["type_key"] == "book" and r["work_id"] == book.pk for r in payload["results"]
    )


def test_relation_search_excludes(client_logged_in):
    book = BookFactory(title="Foundation")
    response = client_logged_in.get(
        reverse("vor_archives:artworks:relation_search"),
        {"q": "Found", "exclude_type": "book", "exclude_id": str(book.pk)},
    )
    payload = json.loads(response.content)
    assert all(
        r["work_id"] != book.pk for r in payload["results"] if r["type_key"] == "book"
    )
