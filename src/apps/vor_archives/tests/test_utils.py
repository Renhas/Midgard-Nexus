"""Tests for shared helpers in apps.vor_archives.utils."""

import pytest

from apps.vor_archives.utils import module_base_context, parse_int_list


def test_module_base_context_defaults_and_hide_right():
    ctx = module_base_context("attributes")
    assert ctx["active_section"] == "attributes"
    assert ctx["module_name"]
    assert "hide_right" not in ctx

    hidden_ctx = module_base_context("dashboard", hide_right=True)
    assert hidden_ctx["active_section"] == "dashboard"
    assert hidden_ctx["hide_right"] is True


@pytest.mark.parametrize(
    "raw_values,kwargs,expected",
    [
        pytest.param(["1", "2", "1"], {}, [1, 2, 1], id="preserves-duplicates"),
        pytest.param(
            ["1", "2", "1"],
            {"unique": True},
            [1, 2],
            id="unique-preserves-order",
        ),
        pytest.param(
            ["1, 2, 2, 3"],
            {"comma_separated": True, "unique": True},
            [1, 2, 3],
            id="comma-separated-unique",
        ),
        pytest.param(
            ["", "abc", None, "4"],
            {"comma_separated": True},
            [4],
            id="skips-invalid-values",
        ),
    ],
)
def test_parse_int_list(raw_values, kwargs, expected):
    assert parse_int_list(raw_values, **kwargs) == expected
