"""Tests for apps.vor_archives.artworks.services.catalog."""

import pytest

from apps.vor_archives.artworks.services.catalog import chip_payload, prefetch_work
from apps.vor_archives.tests.factories import PersonFactory, UserWorkFactory


# ─── chip_payload ───────────────────────────────────────────────────────────


def test_chip_payload_empty():
    assert chip_payload([]) == []


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
    assert chip_payload([person], tip_field) == [
        {"id": person.pk, "name": "Tolkien", "tip": expected_tip}
    ]


# ─── prefetch_work ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_prefetch_work_book_caches_related(book):
    result = prefetch_work(book)
    assert result == "book"
    assert "authors" in book._prefetched_objects_cache
    assert "tags" in book._prefetched_objects_cache
    assert "genres" in book._prefetched_objects_cache
    assert "platforms" not in book._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_game_caches_platforms(game):
    result = prefetch_work(game)
    assert result == "game"
    assert "authors" in game._prefetched_objects_cache
    assert "platforms" in game._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_with_user_work_caches_owned_platforms(user, game):
    uw = UserWorkFactory(user=user, work=game)
    prefetch_work(game, uw)
    assert "owned_platforms" in uw._prefetched_objects_cache
