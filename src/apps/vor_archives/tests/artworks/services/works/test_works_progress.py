"""Tests for apps.vor_archives.artworks.services.works - progress clamping.

Covers clamp_progress_for_work per work type: pages for books, duration
for movies, episode count for TV shows, and no limit for games.
"""

from decimal import Decimal

import pytest

from apps.vor_archives.artworks.services import clamp_progress_for_work
from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db

# ─── clamp_progress_for_work ────────────────────────────────────────────────


def test_clamp_progress_book_caps_at_pages(user, book):
    book.pages = 100
    book.save()
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("150"))

    clamp_progress_for_work(book)

    uw.refresh_from_db()
    assert uw.progress == Decimal("100")


def test_clamp_progress_book_leaves_lower_untouched(user, book):
    book.pages = 100
    book.save()
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))

    clamp_progress_for_work(book)

    uw.refresh_from_db()
    assert uw.progress == Decimal("50")


def test_clamp_progress_movie_uses_duration(user, movie):
    movie.duration_minutes = 120
    movie.save()
    uw = UserWorkFactory(user=user, work=movie, progress=Decimal("200"))

    clamp_progress_for_work(movie)

    uw.refresh_from_db()
    assert uw.progress == Decimal("120")


def test_clamp_progress_tv_show_uses_episode_count(user, tv_show):
    uw = UserWorkFactory(user=user, work=tv_show, progress=Decimal("100"))

    clamp_progress_for_work(tv_show)

    uw.refresh_from_db()
    assert uw.progress == Decimal("10")


def test_clamp_progress_game_does_nothing(user, game):
    uw = UserWorkFactory(user=user, work=game, progress=Decimal("9999"))

    clamp_progress_for_work(game)

    uw.refresh_from_db()
    assert uw.progress == Decimal("9999")
