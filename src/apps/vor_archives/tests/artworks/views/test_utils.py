"""Tests for apps.vor_archives.artworks.views.utils.artworks helpers."""

import pytest
from django.test import RequestFactory

from apps.vor_archives.artworks.views.utils.artworks import (
    _chip_payload,
    _prefetch_work,
    _progress_unit,
    parse_relations_payload,
    progress_meta_for_work,
)
from apps.vor_archives.artworks.views.utils.common import parse_id_list
from apps.vor_archives.constants import FilmTypeChoices
from apps.vor_archives.tests.factories import PersonFactory, UserWorkFactory


# ─── parse_id_list ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "post_data,expected",
    [
        pytest.param({"authors": ["1", "2"]}, [1, 2], id="valid-list"),
        pytest.param({"authors": ["1,2,3"]}, [1, 2, 3], id="comma-separated"),
        pytest.param({"authors": ["1,,2,  ,3,"]}, [1, 2, 3], id="empty-parts-skipped"),
        pytest.param({"authors": ["abc", "1", "xyz"]}, [1], id="invalid-parts-skipped"),
        pytest.param({}, [], id="missing-key"),
    ],
)
def test_parse_id_list(post_data, expected):
    request = RequestFactory().post("/", post_data)
    assert parse_id_list(request, "authors") == expected


# ─── parse_relations_payload ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(None, id="missing-field"),
        pytest.param("", id="empty-string"),
        pytest.param("{bad", id="invalid-json"),
        pytest.param('"string"', id="not-a-list"),
        pytest.param("[1, 2]", id="list-of-non-dicts"),
    ],
)
def test_parse_relations_payload_invalid_returns_empty(payload):
    data = {} if payload is None else {"relations_json": payload}
    request = RequestFactory().post("/", data)
    assert parse_relations_payload(request) == []


@pytest.mark.parametrize(
    "payload,expected",
    [
        pytest.param(
            '[{"type_key": "book", "work_id": 5, "relation_type": "sequel"}]',
            [
                {
                    "id": None,
                    "relation_type": "sequel",
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="valid",
        ),
        pytest.param(
            '[{"type_key": "book", "work_id": 5}]',
            [
                {
                    "id": None,
                    "relation_type": "other",
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="default-relation-type",
        ),
        pytest.param(
            '[{"id": "abc", "type_key": "book", "work_id": 5}]',
            [
                {
                    "id": None,
                    "relation_type": "other",
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="invalid-id-string-to-null",
        ),
        pytest.param(
            '[{"id": 1, "work_id": "abc"}]',
            [
                {
                    "id": 1,
                    "relation_type": "other",
                    "type_key": None,
                    "work_id": None,
                }
            ],
            id="invalid-work-id-string-to-null",
        ),
    ],
)
def test_parse_relations_payload_valid(payload, expected):
    request = RequestFactory().post("/", {"relations_json": payload})
    assert parse_relations_payload(request) == expected


# ─── progress_meta_for_work ─────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixture_name,expected_fn",
    [
        pytest.param(
            "book",
            lambda w: {"maximum": w.pages, "unit": "стр.", "step": 1},
            id="book",
        ),
        pytest.param(
            "movie",
            lambda w: {"maximum": w.duration_minutes, "unit": "мин.", "step": 1},
            id="movie",
        ),
        pytest.param(
            "tv_show",
            lambda w: {"maximum": w.episode_count, "unit": "эп.", "step": 1},
            id="tv-show",
        ),
        pytest.param(
            "game",
            lambda _w: {"maximum": None, "unit": "ч.", "step": 0.5},
            id="game",
        ),
    ],
)
def test_progress_meta_for_work(request, fixture_name, expected_fn):
    work = request.getfixturevalue(fixture_name)
    assert progress_meta_for_work(work) == expected_fn(work)


# ─── _progress_unit ─────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixture_name,expected",
    [
        pytest.param("book", "стр.", id="book"),
        pytest.param("movie", "мин.", id="movie"),
        pytest.param("tv_show", "эп.", id="tv-show"),
        pytest.param("game", "ч.", id="game"),
    ],
)
def test_progress_unit_by_work(request, fixture_name, expected):
    work = request.getfixturevalue(fixture_name)
    assert _progress_unit(work) == expected


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        pytest.param({"type_key": "book"}, "стр.", id="type-book"),
        pytest.param({"type_key": "game"}, "ч.", id="type-game"),
        pytest.param(
            {"type_key": "film", "film_type": FilmTypeChoices.TV_SHOW},
            "эп.",
            id="type-film-tv-show",
        ),
        pytest.param(
            {"type_key": "film", "film_type": FilmTypeChoices.MOVIE},
            "мин.",
            id="type-film-movie",
        ),
        pytest.param({}, "", id="no-args"),
    ],
)
def test_progress_unit_by_type(kwargs, expected):
    assert _progress_unit(**kwargs) == expected


# ─── _chip_payload ──────────────────────────────────────────────────────────


def test_chip_payload_empty():
    assert _chip_payload([]) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tip_field,expected_tip",
    [
        pytest.param("bio", "Author", id="bio-field"),
        pytest.param("missing_attr", "", id="missing-attr"),
    ],
)
def test_chip_payload_person(tip_field, expected_tip):
    person = PersonFactory(name="Tolkien", bio="Author")
    assert _chip_payload([person], tip_field) == [
        {"id": person.pk, "name": "Tolkien", "tip": expected_tip}
    ]


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
def test_prefetch_work_game_caches_platforms(game):
    result = _prefetch_work(game)
    assert result == "game"
    assert "authors" in game._prefetched_objects_cache
    assert "platforms" in game._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_with_user_work_caches_owned_platforms(user, game):
    uw = UserWorkFactory(user=user, work=game)
    _prefetch_work(game, uw)
    assert "owned_platforms" in uw._prefetched_objects_cache
