"""Tests for apps.vor_archives.artworks.forms.QuickUpdateForm."""

from decimal import Decimal

import pytest

from apps.vor_archives.artworks.forms import QuickUpdateForm
from apps.vor_archives.constants import UserWorkStatusChoices


def _form(field, value):
    return QuickUpdateForm(data={"field": field, "value": value})


# ─── field ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("status", UserWorkStatusChoices.PLANNING, id="status"),
        pytest.param("progress", "1", id="progress"),
        pytest.param("rating", "5", id="rating"),
        pytest.param("is_hidden", "1", id="is_hidden"),
        pytest.param("times_completed", "1", id="times_completed"),
        pytest.param("owned_platform", "1", id="owned_platform"),
    ],
)
def test_quick_form_accepts_known_fields(field, value):
    form = _form(field, value)
    assert form.is_valid(), form.errors


def test_quick_form_unknown_field_invalid():
    form = _form("bogus", "1")
    assert not form.is_valid()
    assert "field" in form.errors


def test_quick_form_missing_field_invalid():
    form = QuickUpdateForm(data={"value": "1"})
    assert not form.is_valid()
    assert "field" in form.errors


# ─── status ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value", [choice[0] for choice in UserWorkStatusChoices.choices]
)
def test_quick_form_status_valid(value):
    form = _form("status", value)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == value


def test_quick_form_status_invalid():
    form = _form("status", "bogus")
    assert not form.is_valid()
    assert "value" in form.errors


# ─── progress ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("0", Decimal("0"), id="zero"),
        pytest.param("42.5", Decimal("42.5"), id="fractional"),
        pytest.param("-5", Decimal("0"), id="negative-clamped"),
    ],
)
def test_quick_form_progress(raw, expected):
    form = _form("progress", raw)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == expected


def test_quick_form_progress_invalid():
    form = _form("progress", "abc")
    assert not form.is_valid()
    assert "value" in form.errors


# ─── rating ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("", None, id="empty"),
        pytest.param("0", None, id="zero-clears"),
        pytest.param("1", 1, id="min"),
        pytest.param("10", 10, id="max"),
    ],
)
def test_quick_form_rating(raw, expected):
    form = _form("rating", raw)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == expected


@pytest.mark.parametrize("raw", ["-1", "11", "abc", "00"])
def test_quick_form_rating_invalid(raw):
    form = _form("rating", raw)
    assert not form.is_valid()
    assert "value" in form.errors


# ─── is_hidden ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("1", True, id="one"),
        pytest.param("true", True, id="true-lower"),
        pytest.param("True", True, id="true-title"),
        pytest.param("0", False, id="zero"),
        pytest.param("false", False, id="false-lower"),
        pytest.param("", False, id="empty"),
    ],
)
def test_quick_form_is_hidden(raw, expected):
    form = _form("is_hidden", raw)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] is expected


# ─── times_completed ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("0", 0, id="zero"),
        pytest.param("5", 5, id="positive"),
        pytest.param("-3", 0, id="negative-clamped"),
    ],
)
def test_quick_form_times_completed(raw, expected):
    form = _form("times_completed", raw)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == expected


def test_quick_form_times_completed_invalid():
    form = _form("times_completed", "abc")
    assert not form.is_valid()
    assert "value" in form.errors


# ─── owned_platform ─────────────────────────────────────────────────────────


def test_quick_form_owned_platform_valid():
    form = _form("owned_platform", "42")
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == 42


def test_quick_form_owned_platform_invalid():
    form = _form("owned_platform", "abc")
    assert not form.is_valid()
    assert "value" in form.errors
