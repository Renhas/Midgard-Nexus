"""Tests for artwork_add view: new work form for book, film and game types."""

import json

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from apps.vor_archives.models import Book, Film, WorkRelation
from apps.vor_archives.tests.factories import (
    BookGenreFactory,
    PersonFactory,
    TagFactory,
)


pytestmark = pytest.mark.django_db


# ─── artwork_add ────────────────────────────────────────────────────────────


def test_add_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:add"))
    assert response.status_code == 302


def test_add_get_context(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:add"))
    assert response.status_code == 200
    add_opts = response.context["add_opts"]
    assert add_opts["workType"] == "book"
    assert "saveUrl" in add_opts
    assert "searchUrl" in add_opts
    assert "previewUrl" in add_opts
    assert "attachUrl" in add_opts
    assert "listUrl" in add_opts
    assert "relationSearchUrl" in add_opts
    assert "relationTypes" in add_opts
    assert "catalogs" in add_opts
    assert "ageChoices" in add_opts
    assert "statusChoices" in add_opts


def test_add_post_unknown_type_400(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"), {"work_type": "nope"}
    )
    assert response.status_code == 400


def test_add_post_valid_book_creates_work(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "book", "title": "New Book", "pages": "100"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["work_type"] == "book"
    assert payload["title"] == "New Book"
    assert payload["progressMax"] == 100
    assert payload["progressUnit"] == "стр."
    assert payload["progressStep"] == 1
    assert Book.objects.filter(pk=payload["work_id"]).exists()


def test_add_post_invalid_book_returns_form_errors(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "book", "title": "", "pages": ""},
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False
    assert "title" in payload["errors"]
    assert "pages" in payload["errors"]


def test_add_post_movie_form_clears_episode_count(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "film",
            "title": "New Movie",
            "duration_minutes": "120",
            "film_type": "movie",
            "episode_count": "5",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)

    film = Film.objects.get(pk=payload["work_id"])
    assert film.episode_count is None


# ─── artwork_add: type-specific ─────────────────────────────────────────────


def test_add_post_tv_show(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "film",
            "title": "New Show",
            "duration_minutes": "60",
            "film_type": "tv_show",
            "episode_count": "10",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["progressMax"] == 10
    assert payload["progressUnit"] == "эп."
    assert payload["progressStep"] == 1


def test_add_post_game(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "game", "title": "New Game"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["progressMax"] is None
    assert payload["progressUnit"] == "ч."
    assert payload["progressStep"] == 0.5


def test_add_post_with_m2m_and_relations(client_logged_in, book):
    person = PersonFactory()
    tag = TagFactory()
    genre = BookGenreFactory()
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "authors": [str(person.pk)],
            "tags": [str(tag.pk)],
            "genres": [str(genre.pk)],
            "relations_json": json.dumps(
                [
                    {
                        "type_key": "book",
                        "work_id": book.pk,
                        "relation_type": "sequel",
                    }
                ]
            ),
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    new_book = Book.objects.get(pk=payload["work_id"])
    assert list(new_book.authors.all()) == [person]
    assert list(new_book.tags.all()) == [tag]
    assert list(new_book.genres.all()) == [genre]
    ct = ContentType.objects.get_for_model(Book)
    assert WorkRelation.objects.filter(
        source_content_type=ct,
        source_object_id=new_book.pk,
        target_content_type=ct,
        target_object_id=book.pk,
    ).exists()


def test_add_post_malformed_authors_list(client_logged_in):
    person = PersonFactory()
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "authors": f"abc,,{person.pk}",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    new_book = Book.objects.get(pk=payload["work_id"])
    assert list(new_book.authors.all()) == [person]


@pytest.mark.parametrize(
    "relations_json",
    [
        pytest.param("{bad", id="invalid-json"),
        pytest.param('"string"', id="not-a-list"),
        pytest.param("[1, 2]", id="list-of-non-dicts"),
        pytest.param('[{"id": "abc"}]', id="invalid-id-string"),
    ],
)
def test_add_post_malformed_relations_json_ok(client_logged_in, relations_json):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "relations_json": relations_json,
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
