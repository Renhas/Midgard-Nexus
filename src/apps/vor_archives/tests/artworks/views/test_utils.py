"""Tests for apps.vor_archives.artworks.views.utils.artworks helpers."""

import json

import pytest
from django.test import RequestFactory

from apps.vor_archives.artworks.views.utils.artworks import (
    _chip_payload,
    _id_list,
    _prefetch_work,
    _progress_unit,
    parse_id_list,
    parse_relations_payload,
    progress_meta_for_work,
)
from apps.vor_archives.constants import FilmTypeChoices
from apps.vor_archives.tests.factories import (
    GameFactory,
    PersonFactory,
    UserWorkFactory,
)


# ─── parse_id_list ──────────────────────────────────────────────────────────


def test_parse_id_list_valid():
    rf = RequestFactory()
    request = rf.post("/", {"authors": ["1", "2"]})
    assert parse_id_list(request, "authors") == [1, 2]


def test_parse_id_list_comma_separated():
    rf = RequestFactory()
    request = rf.post("/", {"authors": ["1,2,3"]})
    assert parse_id_list(request, "authors") == [1, 2, 3]


def test_parse_id_list_empty_and_whitespace_parts_skipped():
    rf = RequestFactory()
    request = rf.post("/", {"authors": ["1,,2,  ,3,"]})
    assert parse_id_list(request, "authors") == [1, 2, 3]


def test_parse_id_list_invalid_parts_skipped():
    rf = RequestFactory()
    request = rf.post("/", {"authors": ["abc", "1", "xyz"]})
    assert parse_id_list(request, "authors") == [1]


def test_parse_id_list_missing_key():
    rf = RequestFactory()
    request = rf.post("/", {})
    assert parse_id_list(request, "authors") == []


# ─── parse_relations_payload ────────────────────────────────────────────────


def test_parse_relations_payload_missing_field():
    rf = RequestFactory()
    request = rf.post("/", {})
    assert parse_relations_payload(request) == []


def test_parse_relations_payload_empty_string():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": ""})
    assert parse_relations_payload(request) == []


def test_parse_relations_payload_invalid_json():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": "{bad"})
    assert parse_relations_payload(request) == []


def test_parse_relations_payload_not_a_list():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": '"string"'})
    assert parse_relations_payload(request) == []


def test_parse_relations_payload_list_of_non_dicts_skipped():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": "[1, 2]"})
    assert parse_relations_payload(request) == []


def test_parse_relations_payload_valid():
    rf = RequestFactory()
    request = rf.post(
        "/",
        {
            "relations_json": json.dumps(
                [
                    {
                        "type_key": "book",
                        "work_id": 5,
                        "relation_type": "sequel",
                    }
                ]
            )
        },
    )
    result = parse_relations_payload(request)
    assert result == [
        {
            "id": None,
            "relation_type": "sequel",
            "type_key": "book",
            "work_id": 5,
        }
    ]


def test_parse_relations_payload_default_relation_type():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": '[{"type_key": "book", "work_id": 5}]'})
    result = parse_relations_payload(request)
    assert result[0]["relation_type"] == "other"


def test_parse_relations_payload_invalid_id_string_null():
    rf = RequestFactory()
    request = rf.post(
        "/",
        {"relations_json": '[{"id": "abc", "type_key": "book", "work_id": 5}]'},
    )
    result = parse_relations_payload(request)
    assert result[0]["id"] is None
    assert result[0]["work_id"] == 5


def test_parse_relations_payload_invalid_work_id_string_null():
    rf = RequestFactory()
    request = rf.post("/", {"relations_json": '[{"id": 1, "work_id": "abc"}]'})
    result = parse_relations_payload(request)
    assert result[0]["work_id"] is None
    assert result[0]["id"] == 1


# ─── progress_meta_for_work ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_progress_meta_for_book(book):
    assert progress_meta_for_work(book) == {
        "maximum": book.pages,
        "unit": "стр.",
        "step": 1,
    }


@pytest.mark.django_db
def test_progress_meta_for_movie(movie):
    assert progress_meta_for_work(movie) == {
        "maximum": movie.duration_minutes,
        "unit": "мин.",
        "step": 1,
    }


@pytest.mark.django_db
def test_progress_meta_for_tv_show(tv_show):
    assert progress_meta_for_work(tv_show) == {
        "maximum": tv_show.episode_count,
        "unit": "эп.",
        "step": 1,
    }


@pytest.mark.django_db
def test_progress_meta_for_game(game):
    assert progress_meta_for_work(game) == {
        "maximum": None,
        "unit": "ч.",
        "step": 0.5,
    }


# ─── _progress_unit ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_progress_unit_book(book):
    assert _progress_unit(book) == "стр."


@pytest.mark.django_db
def test_progress_unit_movie(movie):
    assert _progress_unit(movie) == "мин."


@pytest.mark.django_db
def test_progress_unit_tv_show(tv_show):
    assert _progress_unit(tv_show) == "эп."


@pytest.mark.django_db
def test_progress_unit_game(game):
    assert _progress_unit(game) == "ч."


def test_progress_unit_by_type_and_film_type():
    assert _progress_unit(type_key="book") == "стр."
    assert _progress_unit(type_key="game") == "ч."
    assert _progress_unit(type_key="film", film_type=FilmTypeChoices.TV_SHOW) == "эп."
    assert _progress_unit(type_key="film", film_type=FilmTypeChoices.MOVIE) == "мин."


def test_progress_unit_no_args():
    assert _progress_unit() == ""


# ─── _chip_payload ──────────────────────────────────────────────────────────


def test_chip_payload_empty():
    assert _chip_payload([]) == []


@pytest.mark.django_db
def test_chip_payload_person_with_bio():
    person = PersonFactory(name="Tolkien", bio="Author")
    result = _chip_payload([person], "bio")
    assert result == [{"id": person.pk, "name": "Tolkien", "tip": "Author"}]


@pytest.mark.django_db
def test_chip_payload_default_tip_field():
    person = PersonFactory(name="X", bio="")
    result = _chip_payload([person])
    assert result == [{"id": person.pk, "name": "X", "tip": ""}]


# ─── _id_list ───────────────────────────────────────────────────────────────


def test_id_list_valid():
    rf = RequestFactory()
    request = rf.get("/?tags=1&tags=2")
    assert _id_list(request, "tags") == [1, 2]


def test_id_list_empty():
    rf = RequestFactory()
    request = rf.get("/")
    assert _id_list(request, "tags") == []


def test_id_list_invalid_skipped():
    rf = RequestFactory()
    request = rf.get("/?tags=abc&tags=1&tags=x")
    assert _id_list(request, "tags") == [1]


# ─── _prefetch_work ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_prefetch_work_book_caches_related(book):
    result = _prefetch_work(book)
    assert result == "book"
    assert "authors" in book._prefetched_objects_cache
    assert "tags" in book._prefetched_objects_cache
    assert "genres" in book._prefetched_objects_cache
    assert "platforms" not in book._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_game_caches_platforms():
    game = GameFactory()
    result = _prefetch_work(game)
    assert result == "game"
    assert "authors" in game._prefetched_objects_cache
    assert "platforms" in game._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_with_user_work_caches_owned_platforms(user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game)
    _prefetch_work(game, uw)
    assert "owned_platforms" in uw._prefetched_objects_cache
