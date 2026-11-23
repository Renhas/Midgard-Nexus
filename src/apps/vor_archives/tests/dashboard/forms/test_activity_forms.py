"""Tests for apps.vor_archives.dashboard forms."""

import pytest

from apps.vor_archives.dashboard.forms import (
    FeedPaginationForm,
    HeatmapFilterForm,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ({}, None),
        ({"year": ""}, None),
        ({"year": None}, None),
        ({"year": "nope"}, None),
        ({"year": "1800"}, None),
        ({"year": "2101"}, None),
        ({"year": "2024.5"}, None),
        ({"year": "1970"}, 1970),
        ({"year": "2026"}, 2026),
        ({"year": "2100"}, 2100),
        ({"year": " 2026 "}, 2026),
    ],
)
def test_heatmap_filter_form_get_year(raw, expected):
    form = HeatmapFilterForm(raw)
    assert form.get_year() == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ({}, 0),
        ({"offset": ""}, 0),
        ({"offset": None}, 0),
        ({"offset": "abc"}, 0),
        ({"offset": "-5"}, 0),
        ({"offset": "-1"}, 0),
        ({"offset": "1.5"}, 0),
        ({"offset": "0"}, 0),
        ({"offset": "30"}, 30),
        ({"offset": " 60 "}, 60),
    ],
)
def test_feed_pagination_form_get_offset(raw, expected):
    form = FeedPaginationForm(raw)
    assert form.get_offset() == expected
