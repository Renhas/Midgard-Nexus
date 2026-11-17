"""Tests for apps.vor_archives.artworks.views.utils helpers."""

import pytest
from django.test import RequestFactory

from apps.vor_archives.artworks.views.utils.artworks import (
    progress_meta_for_work,
)
from apps.vor_archives.artworks.views.utils.common import parse_id_list


# ─── parse_id_list ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "post_data,expected",
    [
        pytest.param({"authors": ["1", "2"]}, [1, 2], id="valid-list"),
        pytest.param({"authors": ["1,2,3"]}, [1, 2, 3], id="comma-separated"),
        pytest.param({"authors": ["1,,2,  ,3,"]}, [1, 2, 3], id="empty-parts-skipped"),
        pytest.param({"authors": ["abc", "1", "xyz"]}, [1], id="invalid-parts-skipped"),
        pytest.param({}, [], id="missing-key"),
    ],
)
def test_parse_id_list(post_data, expected):
    request = RequestFactory().post("/", post_data)
    assert parse_id_list(request, "authors") == expected


# ─── progress_meta_for_work ─────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixture_name,expected_fn",
    [
        pytest.param(
            "book",
            lambda w: {"maximum": w.pages, "unit": "стр.", "step": 1},
            id="book",
        ),
        pytest.param(
            "movie",
            lambda w: {"maximum": w.duration_minutes, "unit": "мин.", "step": 1},
            id="movie",
        ),
        pytest.param(
            "tv_show",
            lambda w: {"maximum": w.episode_count, "unit": "эп.", "step": 1},
            id="tv-show",
        ),
        pytest.param(
            "game",
            lambda _w: {"maximum": None, "unit": "ч.", "step": 0.5},
            id="game",
        ),
    ],
)
def test_progress_meta_for_work(request, fixture_name, expected_fn):
    work = request.getfixturevalue(fixture_name)
    assert progress_meta_for_work(work) == expected_fn(work)
