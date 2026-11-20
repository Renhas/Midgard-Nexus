"""Tests for apps.vor_archives.dashboard.services.attrs."""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.dashboard.services.attrs import attrs_payload
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmGenreFactory,
    GameFactory,
    GameGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
)


@pytest.mark.django_db
def test_attrs_payload_genre_name_collision(user, book, movie, game):
    shared = "Fantasy"
    unique = "Action"
    book.genres.add(BookGenreFactory(name=shared))
    movie.genres.add(FilmGenreFactory(name=shared))
    game.genres.add(GameGenreFactory(name=unique))
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    genre_names = {item["name"] for item in attrs["genres"]}

    assert "Fantasy (Книги)" in genre_names
    assert "Fantasy (Фильмы)" in genre_names
    assert "Action (Игры)" in genre_names


@pytest.mark.django_db
def test_attrs_payload_tags_counts_and_sorting(user, book, game):
    tags = {name: TagFactory(name=name) for name in ["alpha", "beta", "gamma"]}
    book.tags.add(*tags.values())
    game.tags.add(tags["beta"])
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    tag_counts = {item["name"]: item["count"] for item in attrs["tags"]}

    assert tag_counts == {"alpha": 1, "beta": 2, "gamma": 1}
    assert [item["name"] for item in attrs["tags"]] == [
        "beta",
        "alpha",
        "gamma",
    ]


@pytest.mark.django_db
def test_attrs_payload_persons_counts_and_sorting(user, book, game):
    authors = {
        name: PersonFactory(name=name) for name in ["Author A", "Author B", "Author C"]
    }
    book.authors.add(*authors.values())
    game.authors.add(authors["Author B"])
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    person_counts = {item["name"]: item["count"] for item in attrs["persons"]}

    assert person_counts == {"Author A": 1, "Author B": 2, "Author C": 1}
    assert [item["name"] for item in attrs["persons"]] == [
        "Author B",
        "Author A",
        "Author C",
    ]


@pytest.mark.django_db
def test_attrs_payload_platform_counts_and_sorting(user):
    platforms = {name: PlatformFactory(name=name) for name in ["PC", "Xbox", "Switch"]}
    first_game = GameFactory()
    second_game = GameFactory()
    first_game.platforms.add(*platforms.values())
    second_game.platforms.add(platforms["Xbox"])
    UserWorkFactory(user=user, work=first_game)
    UserWorkFactory(user=user, work=second_game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    platforms_counts = {item["name"]: item["count"] for item in attrs["platforms"]}

    assert platforms_counts == {"PC": 1, "Xbox": 2, "Switch": 1}
    assert [item["name"] for item in attrs["platforms"]] == ["Xbox", "PC", "Switch"]


@pytest.mark.django_db
def test_attrs_payload_genres_counts_and_sorting(user):
    genres = {
        name: GameGenreFactory(name=name) for name in ["Action", "RPG", "Adventure"]
    }
    first_game = GameFactory()
    second_game = GameFactory()
    first_game.genres.add(*genres.values())
    second_game.genres.add(genres["RPG"])
    UserWorkFactory(user=user, work=first_game)
    UserWorkFactory(user=user, work=second_game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    genres_counts = {item["name"]: item["count"] for item in attrs["genres"]}

    assert genres_counts == {"Action (Игры)": 1, "RPG (Игры)": 2, "Adventure (Игры)": 1}
    assert [item["name"] for item in attrs["genres"]] == [
        "RPG (Игры)",
        "Action (Игры)",
        "Adventure (Игры)",
    ]


@pytest.mark.django_db
def test_attrs_payload_excludes_orphans_and_foreign(user, game):
    TagFactory(name="orphan-tag")
    PersonFactory(name="orphan-author")
    PlatformFactory(name="orphan-platform")
    GameGenreFactory(name="orphan-genre")

    game.tags.add(TagFactory(name="alpha"))
    game.authors.add(PersonFactory(name="Author A"))
    game.platforms.add(PlatformFactory(name="PC"))
    game.genres.add(GameGenreFactory(name="RPG"))

    UserWorkFactory(user=user, work=game)

    other = UserFactory()
    other_book = BookFactory()
    other_book.tags.add(TagFactory(name="foreign-tag"))
    UserWorkFactory(user=other, work=other_book)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]

    tag_names = {item["name"] for item in attrs["tags"]}
    person_names = {item["name"] for item in attrs["persons"]}
    platform_names = {item["name"] for item in attrs["platforms"]}
    genre_names = {item["name"] for item in attrs["genres"]}

    assert "alpha" in tag_names
    assert "Author A" in person_names
    assert "PC" in platform_names
    assert "RPG (Игры)" in genre_names
    assert "orphan-tag" not in tag_names
    assert "orphan-author" not in person_names
    assert "orphan-platform" not in platform_names
    assert not any(name.startswith("orphan-genre") for name in genre_names)
    assert "foreign-tag" not in tag_names
