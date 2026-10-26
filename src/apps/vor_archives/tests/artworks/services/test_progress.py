"""Tests for apps.vor_archives.artworks.services.progress - unit/step metadata."""

import pytest

from apps.vor_archives.artworks.services.progress import (
    ProgressMeta,
    work_progress,
)
from apps.vor_archives.constants import FilmTypeChoices

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
