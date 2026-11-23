"""Tests for apps.vor_archives.progress."""

from decimal import Decimal

import pytest

from apps.vor_archives.progress import (
    ProgressMeta,
    clamp_progress_for_work,
    work_progress,
    progress_spent,
)
from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db

# ─── work_progress ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "fixture_name,expected_fn",
    [
        pytest.param("book", lambda w: ProgressMeta(w.pages, "стр.", 1), id="book"),
        pytest.param(
            "movie",
            lambda w: ProgressMeta(w.duration_minutes, "мин.", 1),
            id="movie",
        ),
        pytest.param(
            "tv_show",
            lambda w: ProgressMeta(w.episode_count, "эп.", 1),
            id="tv-show",
        ),
        pytest.param("game", lambda _w: ProgressMeta(None, "ч.", 0.5), id="game"),
    ],
)
def test_work_progress(request, fixture_name, expected_fn):
    work = request.getfixturevalue(fixture_name)
    assert work_progress(work) == expected_fn(work)


def test_work_progress_none():
    assert work_progress(None) == ProgressMeta(None, "", 1)


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


# ─── progress_spent ────────────────────────────────────────────────


@pytest.mark.django_db
def test_tv_show_hours_uses_episode_duration_times_progress(user, tv_show):
    tv_show.duration_minutes = 45
    tv_show.save()
    user_work = UserWorkFactory(user=user, work=tv_show, progress=Decimal("4"))

    type_key, amount, unit = progress_spent(user_work)

    assert type_key == "film"
    assert unit == "ч."
    assert amount == 3.0


@pytest.mark.django_db
def test_movie_hours_use_progress_minutes(user, movie):
    movie.duration_minutes = 90
    movie.save()
    user_work = UserWorkFactory(user=user, work=movie, progress=Decimal("90"))

    _, amount, unit = progress_spent(user_work)

    assert unit == "ч."
    assert amount == 1.5


@pytest.mark.django_db
def test_book_and_game_progress_passthrough(user, book, game):
    book_uw = UserWorkFactory(user=user, work=book, progress=Decimal("150"))
    game_uw = UserWorkFactory(user=user, work=game, progress=Decimal("12.5"))

    assert progress_spent(book_uw) == ("book", 150.0, "стр.")
    assert progress_spent(game_uw) == ("game", 12.5, "ч.")


@pytest.mark.django_db
def test_progress_spent_edge_cases(user, book, tv_show):
    default_progress_uw = UserWorkFactory(user=user, work=book)
    assert progress_spent(default_progress_uw) == ("book", 0.0, "стр.")

    tv_show.duration_minutes = 0
    tv_show.save()
    zero_duration_tv = UserWorkFactory(user=user, work=tv_show, progress=Decimal("5"))
    assert progress_spent(zero_duration_tv) == ("film", 0.0, "ч.")
