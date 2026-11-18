"""Tests for apps.vor_archives.attributes.services.mutations."""

import pytest

from apps.vor_archives.attributes.services.mutations import (
    build_genre_delete_items,
    build_simple_delete_items,
    delete_attrs,
    resolve_delete_items,
)
from apps.vor_archives.models import Book, BookGenre, FilmGenre, Tag
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── build_genre_delete_items & build_simple_delete_items ───────────────────


def test_build_genre_delete_items_skips_missing_and_counts_works():
    bg = BookGenreFactory(name="Fantasy")
    fg = FilmGenreFactory(name="Noir")
    book = BookFactory()
    book.genres.add(bg)

    items = build_genre_delete_items(
        [("book", bg.pk), ("book", 999999), ("film", fg.pk)]
    )

    assert items == [
        {
            "key": f"book:{bg.pk}",
            "type_key": "book",
            "pk": bg.pk,
            "name": "Fantasy",
            "type_label": "Книги",
            "work_count": 1,
            "obj": bg,
        },
        {
            "key": f"film:{fg.pk}",
            "type_key": "film",
            "pk": fg.pk,
            "name": "Noir",
            "type_label": "Фильмы",
            "work_count": 0,
            "obj": fg,
        },
    ]


def test_build_simple_delete_items_skips_missing_and_counts_works():
    tag = TagFactory(name="Classic")
    book = BookFactory()
    book.tags.add(tag)

    items = build_simple_delete_items("tags", [tag.pk, 999999])

    assert items == [
        {
            "key": str(tag.pk),
            "pk": tag.pk,
            "name": "Classic",
            "work_count": 1,
            "obj": tag,
        }
    ]


# ─── resolve_delete_items ───────────────────────────────────────────────────


def test_resolve_delete_items_genres_and_simple():
    bg = BookGenreFactory()
    person = PersonFactory()
    platform = PlatformFactory()

    assert [i["obj"] for i in resolve_delete_items("genres", [f"book:{bg.pk}"])] == [bg]
    assert [i["obj"] for i in resolve_delete_items("persons", [str(person.pk)])] == [
        person
    ]
    assert [
        i["obj"] for i in resolve_delete_items("platforms", [str(platform.pk)])
    ] == [platform]


def test_resolve_delete_items_unknown_kind_raises():
    with pytest.raises(ValueError, match="Unknown attribute kind"):
        resolve_delete_items("unknown", ["1"])


# ─── delete_attrs ───────────────────────────────────────────────────────────


def test_delete_attrs_simple_detaches_from_works_without_deleting_work():
    tag1 = TagFactory()
    tag2 = TagFactory()
    book = BookFactory()
    book.tags.add(tag1, tag2)

    deleted_count = delete_attrs("tags", [f"{tag1.pk},999999"])

    assert deleted_count == 1
    assert not Tag.objects.filter(pk=tag1.pk).exists()
    assert Tag.objects.filter(pk=tag2.pk).exists()
    assert Book.objects.filter(pk=book.pk).exists()
    assert list(book.tags.all()) == [tag2]


def test_delete_attrs_genres_deletes_across_types():
    bg = BookGenreFactory()
    fg = FilmGenreFactory()
    untouched = BookGenreFactory()

    deleted_count = delete_attrs("genres", [f"book:{bg.pk}", f"film:{fg.pk}"])

    assert deleted_count == 2
    assert not BookGenre.objects.filter(pk=bg.pk).exists()
    assert not FilmGenre.objects.filter(pk=fg.pk).exists()
    assert BookGenre.objects.filter(pk=untouched.pk).exists()


def test_delete_attrs_unknown_kind_raises():
    with pytest.raises(ValueError, match="Unknown attribute kind"):
        delete_attrs("unknown", ["1"])
