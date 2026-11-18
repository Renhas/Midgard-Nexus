"""Tests for GenreForm in apps.vor_archives.attributes.forms."""

import pytest

from apps.vor_archives.attributes.forms import GenreForm
from apps.vor_archives.models import BookGenre, FilmGenre, GameGenre
from apps.vor_archives.tests.factories import (
    BookGenreFactory,
    FilmGenreFactory,
    GameGenreFactory,
)

pytestmark = pytest.mark.django_db


# ─── Инициализация и блокировка типа ────────────────────────────────────────


def test_genre_form_widgets_and_initial():
    form = GenreForm(initial_type="film")
    assert list(form.fields) == ["name", "type_key", "description"]
    assert form.fields["type_key"].widget.attrs["class"] == "form-select"
    assert form.fields["name"].widget.attrs["class"] == "form-control"
    assert form.fields["description"].widget.attrs["class"] == "form-control"
    assert form.initial == {"type_key": "film"}
    assert not form.fields["type_key"].disabled


def test_genre_form_from_instance_infers_type_and_locks():
    genre = GameGenreFactory(name="RPG", description="Role-playing")
    form = GenreForm(instance=genre, lock_type=True)

    assert form.fixed_type == "game"
    assert form.initial == {
        "name": "RPG",
        "description": "Role-playing",
        "type_key": "game",
    }
    assert form.fields["type_key"].disabled is True
    assert form.fields["type_key"].required is False


# ─── Валидация clean_name ───────────────────────────────────────────────────


@pytest.mark.parametrize("raw_name", ["", "   "])
def test_genre_form_rejects_blank_name(raw_name):
    form = GenreForm(data={"type_key": "book", "name": raw_name})
    assert not form.is_valid()
    assert form.errors["name"] == ["Обязательное поле."]


def test_genre_form_uniqueness_scoped_by_type():
    BookGenreFactory(name="Fantasy")

    # Дубликат внутри того же типа (book) — ошибка
    dup_book = GenreForm(data={"type_key": "book", "name": "  FANTASY  "})
    assert not dup_book.is_valid()
    assert dup_book.errors["name"] == ["Жанр с таким названием уже существует"]

    # Такое же имя в другом типе (film) — разрешено
    valid_film = GenreForm(data={"type_key": "film", "name": "Fantasy"})
    assert valid_film.is_valid()


def test_genre_form_edit_allows_same_name_for_self_but_rejects_other():
    g1 = FilmGenreFactory(name="Noir")
    FilmGenreFactory(name="Thriller")

    same_form = GenreForm(
        data={"name": "noir", "description": "Dark"},
        instance=g1,
        lock_type=True,
        initial_type="film",
    )
    assert same_form.is_valid()

    conflict_form = GenreForm(
        data={"name": "THRILLER"},
        instance=g1,
        lock_type=True,
        initial_type="film",
    )
    assert not conflict_form.is_valid()
    assert conflict_form.errors["name"] == ["Жанр с таким названием уже существует"]


# ─── save() и защита от подмены типа ────────────────────────────────────────


@pytest.mark.parametrize(
    "type_key,expected_model",
    [
        pytest.param("book", BookGenre, id="book"),
        pytest.param("film", FilmGenre, id="film"),
        pytest.param("game", GameGenre, id="game"),
    ],
)
def test_genre_form_save_creates_correct_model(type_key, expected_model):
    form = GenreForm(
        data={"type_key": type_key, "name": "  Adventure  ", "description": "Desc"}
    )
    assert form.is_valid()
    obj, saved_type = form.save()

    assert saved_type == type_key
    assert isinstance(obj, expected_model)
    assert obj.pk is not None
    assert obj.name == "Adventure"
    assert obj.description == "Desc"


def test_genre_form_locked_type_ignores_tampered_post_type():
    genre = BookGenreFactory(name="Old", description="")
    # Попытка подменить type_key в POST на "film" при lock_type=True
    form = GenreForm(
        data={"type_key": "film", "name": "New", "description": "Updated"},
        instance=genre,
        lock_type=True,
        initial_type="book",
    )
    assert form.is_valid()
    obj, saved_type = form.save()

    assert saved_type == "book"
    assert isinstance(obj, BookGenre)
    assert obj.pk == genre.pk
    assert obj.name == "New"
    assert FilmGenre.objects.count() == 0
