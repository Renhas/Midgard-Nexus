"""Tests for apps.vor_archives.attributes.services.queries."""

import pytest

from apps.vor_archives.attributes.services.queries import (
    genre_work_count,
    get_genre,
    get_simple_attr,
    list_genre_groups,
    list_simple_attrs,
    simple_work_count,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmFactory,
    FilmGenreFactory,
    GameFactory,
    GameGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── get_genre & get_simple_attr ────────────────────────────────────────────


@pytest.mark.parametrize(
    "type_key,factory_cls",
    [
        pytest.param("book", BookGenreFactory, id="book"),
        pytest.param("film", FilmGenreFactory, id="film"),
        pytest.param("game", GameGenreFactory, id="game"),
    ],
)
def test_get_genre_found(type_key, factory_cls):
    genre = factory_cls()
    assert get_genre(type_key, genre.pk) == genre


@pytest.mark.parametrize(
    "type_key,pk",
    [
        pytest.param("book", 999999, id="missing-pk"),
        pytest.param("unknown", 1, id="unknown-type-key"),
        pytest.param(None, 1, id="none-type-key"),
    ],
)
def test_get_genre_returns_none(type_key, pk):
    assert get_genre(type_key, pk) is None


@pytest.mark.parametrize(
    "kind,factory_cls",
    [
        pytest.param("tags", TagFactory, id="tags"),
        pytest.param("persons", PersonFactory, id="persons"),
        pytest.param("platforms", PlatformFactory, id="platforms"),
    ],
)
def test_get_simple_attr_found(kind, factory_cls):
    obj = factory_cls()
    assert get_simple_attr(kind, obj.pk) == obj


@pytest.mark.parametrize(
    "kind,pk",
    [
        pytest.param("tags", 999999, id="missing-pk"),
        pytest.param("genres", 1, id="genres-not-simple"),
        pytest.param("unknown", 1, id="unknown-kind"),
    ],
)
def test_get_simple_attr_returns_none(kind, pk):
    assert get_simple_attr(kind, pk) is None


# ─── genre_work_count & simple_work_count ───────────────────────────────────


def test_genre_work_count_zero_and_multiple():
    genre = BookGenreFactory()
    assert genre_work_count(genre) == 0

    b1 = BookFactory()
    b2 = BookFactory()
    b1.genres.add(genre)
    b2.genres.add(genre)

    assert genre_work_count(genre) == 2
    assert genre_work_count(genre, type_key="book") == 2


def test_simple_work_count_tags_and_persons_across_all_work_types():
    tag = TagFactory()
    person = PersonFactory()
    assert simple_work_count(tag, "tags") == 0
    assert simple_work_count(person, "persons") == 0

    book = BookFactory()
    film = FilmFactory()
    game = GameFactory()

    book.tags.add(tag)
    film.tags.add(tag)
    game.tags.add(tag)

    book.authors.add(person)
    film.authors.add(person)

    assert simple_work_count(tag, "tags") == 3
    assert simple_work_count(person, "persons") == 2


def test_simple_work_count_platforms_only_games():
    platform = PlatformFactory()
    assert simple_work_count(platform, "platforms") == 0

    g1 = GameFactory()
    g2 = GameFactory()
    g1.platforms.add(platform)
    g2.platforms.add(platform)

    assert simple_work_count(platform, "platforms") == 2


# ─── list_genre_groups ──────────────────────────────────────────────────────


def test_list_genre_groups_empty():
    groups, total = list_genre_groups()
    assert total == 0
    assert [(g["type_key"], g["items"]) for g in groups] == [
        ("book", []),
        ("film", []),
        ("game", []),
    ]


def test_list_genre_groups_ordering_and_counts():
    BookGenreFactory(name="Zeta")
    bg_a = BookGenreFactory(name="Alpha")
    fg = FilmGenreFactory(name="Drama")
    GameGenreFactory(name="RPG")

    b1 = BookFactory()
    b2 = BookFactory()
    b1.genres.add(bg_a)
    b2.genres.add(bg_a)

    groups, total = list_genre_groups()
    by_type = {g["type_key"]: g["items"] for g in groups}

    assert total == 4
    assert [i["name"] for i in by_type["book"]] == ["Alpha", "Zeta"]
    assert by_type["book"][0] == {
        "key": f"book:{bg_a.pk}",
        "pk": bg_a.pk,
        "type_key": "book",
        "name": "Alpha",
        "work_count": 2,
    }
    assert by_type["book"][1]["work_count"] == 0
    assert [i["key"] for i in by_type["film"]] == [f"film:{fg.pk}"]
    assert len(by_type["game"]) == 1


def test_list_genre_groups_query_filters_items_but_preserves_total():
    BookGenreFactory(name="Dark Fantasy")
    BookGenreFactory(name="Sci-Fi")
    FilmGenreFactory(name="fantasy")

    groups, total = list_genre_groups(query="  FANTASY  ")
    by_type = {g["type_key"]: g["items"] for g in groups}

    assert total == 3
    assert [i["name"] for i in by_type["book"]] == ["Dark Fantasy"]
    assert [i["name"] for i in by_type["film"]] == ["fantasy"]
    assert by_type["game"] == []


# ─── list_simple_attrs ──────────────────────────────────────────────────────


def test_list_simple_attrs_ordering_and_distinct_counts():
    t_b = TagFactory(name="Beta")
    t_a = TagFactory(name="Alpha")

    book = BookFactory()
    film = FilmFactory()
    game = GameFactory()
    book.tags.add(t_a, t_b)
    film.tags.add(t_a)
    game.tags.add(t_a)

    items, total = list_simple_attrs("tags")

    assert total == 2
    assert items == [
        {"key": str(t_a.pk), "pk": t_a.pk, "name": "Alpha", "work_count": 3},
        {"key": str(t_b.pk), "pk": t_b.pk, "name": "Beta", "work_count": 1},
    ]


def test_list_simple_attrs_empty():
    items, total = list_simple_attrs("tags")
    assert total == 0
    assert items == []


def test_list_simple_attrs_query_filters_items_but_preserves_total():
    PlatformFactory(name="PlayStation 5")
    PlatformFactory(name="Xbox Series X")

    items, total = list_simple_attrs("platforms", query="  station ")

    assert total == 2
    assert [i["name"] for i in items] == ["PlayStation 5"]
