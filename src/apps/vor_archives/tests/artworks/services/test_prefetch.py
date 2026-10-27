"""Tests for apps.vor_archives.artworks.services.prefetch."""

import pytest

from apps.vor_archives.artworks.services.prefetch import (
    prefetch_user_works,
    prefetch_work_relations,
    prefetch_work_with_user_work,
)
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import UserWorkFactory


# ─── prefetch_work_relations ────────────────────────────────────────────────


@pytest.mark.django_db
def test_prefetch_work_relations_book_common_only(book):
    prefetch_work_relations([book])
    cache = book._prefetched_objects_cache
    assert "tags" in cache
    assert "genres" in cache
    assert "authors" not in cache
    assert "platforms" not in cache


@pytest.mark.django_db
def test_prefetch_work_relations_with_authors(book):
    prefetch_work_relations([book], with_authors=True)
    assert "authors" in book._prefetched_objects_cache


@pytest.mark.django_db
def test_prefetch_work_relations_game_includes_platforms(game):
    prefetch_work_relations([game])
    cache = game._prefetched_objects_cache
    assert "platforms" in cache
    assert "tags" in cache
    assert "genres" in cache


@pytest.mark.django_db
def test_prefetch_work_relations_skips_none():
    prefetch_work_relations([None])


# ─── prefetch_user_works ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_prefetch_user_works_resolves_work(user, book):
    uw = UserWorkFactory(user=user, work=book)
    items = list(UserWork.objects.filter(pk=uw.pk))
    result = prefetch_user_works(items)
    assert result is items
    assert "work" in items[0]._state.fields_cache


# ─── prefetch_work_with_user_work ───────────────────────────────────────────


@pytest.mark.django_db
def test_prefetch_work_with_user_work_book_returns_type_key(book):
    type_key = prefetch_work_with_user_work(book)
    assert type_key == "book"
    cache = book._prefetched_objects_cache
    assert "authors" in cache
    assert "tags" in cache
    assert "genres" in cache
    assert "platforms" not in cache


@pytest.mark.django_db
def test_prefetch_work_with_user_work_game_caches_platforms_and_owned(game, user):
    uw = UserWorkFactory(user=user, work=game)
    type_key = prefetch_work_with_user_work(game, uw)
    assert type_key == "game"
    assert "platforms" in game._prefetched_objects_cache
    assert "owned_platforms" in uw._prefetched_objects_cache
