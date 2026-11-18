"""Tests for apps.vor_archives.attributes.services.utils."""

import pytest

from apps.vor_archives.attributes.services.utils import (
    genre_composite_id,
    genre_type_key,
    parse_genre_ids,
    parse_simple_ids,
)
from apps.vor_archives.models import BookGenre, FilmGenre, GameGenre, Tag


# ─── genre_type_key ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "model_cls,expected",
    [
        pytest.param(BookGenre, "book", id="book-genre"),
        pytest.param(FilmGenre, "film", id="film-genre"),
        pytest.param(GameGenre, "game", id="game-genre"),
    ],
)
def test_genre_type_key_valid(model_cls, expected):
    obj = model_cls(name="Test")
    assert genre_type_key(obj) == expected


@pytest.mark.parametrize(
    "invalid_obj",
    [
        pytest.param(Tag(name="tag"), id="tag-instance"),
        pytest.param(None, id="none"),
        pytest.param("book", id="string"),
    ],
)
def test_genre_type_key_unknown_raises(invalid_obj):
    with pytest.raises(ValueError, match="Unknown genre model"):
        genre_type_key(invalid_obj)


# ─── genre_composite_id ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "type_key,pk,expected",
    [
        pytest.param("book", 1, "book:1", id="book"),
        pytest.param("film", 42, "film:42", id="film"),
        pytest.param("game", 100, "game:100", id="game"),
    ],
)
def test_genre_composite_id(type_key, pk, expected):
    assert genre_composite_id(type_key, pk) == expected


# ─── parse_genre_ids ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw_values,expected",
    [
        pytest.param(["book:1", "film:2"], [("book", 1), ("film", 2)], id="list"),
        pytest.param(
            ["book:1,film:2,game:3"],
            [("book", 1), ("film", 2), ("game", 3)],
            id="comma-separated",
        ),
        pytest.param(
            [" book:1 , , film:2 , "],
            [("book", 1), ("film", 2)],
            id="whitespace-and-empty-parts",
        ),
        pytest.param(
            ["book:1", "film:2,book:1", "film:2"],
            [("book", 1), ("film", 2)],
            id="deduplicated-preserves-order",
        ),
        pytest.param(
            ["book1", "unknown:1", "book:abc", "book:", ":5", ""],
            [],
            id="invalid-entries-ignored",
        ),
        pytest.param([], [], id="empty-input"),
    ],
)
def test_parse_genre_ids(raw_values, expected):
    assert parse_genre_ids(raw_values) == expected


# ─── parse_simple_ids ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw_values,expected",
    [
        pytest.param(["1", "2", "3"], [1, 2, 3], id="list"),
        pytest.param(["1,2,3"], [1, 2, 3], id="comma-separated"),
        pytest.param([" 1 , , 2 , "], [1, 2], id="whitespace-and-empty-parts"),
        pytest.param(["2", "1,2", "1"], [2, 1], id="deduplicated-preserves-order"),
        pytest.param(["abc", "", "1.5", "None"], [], id="invalid-entries-ignored"),
        pytest.param([], [], id="empty-input"),
    ],
)
def test_parse_simple_ids(raw_values, expected):
    assert parse_simple_ids(raw_values) == expected
