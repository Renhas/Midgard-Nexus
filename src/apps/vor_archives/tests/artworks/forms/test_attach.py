"""Tests for apps.vor_archives forms."""

from decimal import Decimal

import pytest

from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.artworks.forms import AttachWorkForm

# ─── AttachWorkForm ─────────────────────────────────────────────────────────


def test_attach_form_minimal_valid():
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["status"] == UserWorkStatusChoices.PLANNING
    assert form.cleaned_data["rating"] is None
    assert form.cleaned_data["progress"] == Decimal("0")


def test_attach_form_unknown_work_type_invalid():
    form = AttachWorkForm(data={"work_type": "nope", "work_id": "1"})
    assert not form.is_valid()
    assert "work_type" in form.errors


def test_attach_form_missing_work_id_invalid():
    form = AttachWorkForm(data={"work_type": "book"})
    assert not form.is_valid()
    assert "work_id" in form.errors


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("", None, id="empty"),
        pytest.param("0", None, id="zero"),
        pytest.param("1", 1, id="min"),
        pytest.param("10", 10, id="max"),
    ],
)
def test_attach_form_rating_boundaries(raw, expected):
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "rating": raw})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["rating"] == expected


@pytest.mark.parametrize("raw", ["-1", "11", "100"])
def test_attach_form_rating_out_of_range_invalid(raw):
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "rating": raw})
    assert not form.is_valid()
    assert "rating" in form.errors


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("", Decimal("0"), id="empty"),
        pytest.param("0", Decimal("0"), id="zero"),
        pytest.param("5", Decimal("5"), id="positive"),
        pytest.param("-3", Decimal("0"), id="negative-clamped"),
    ],
)
def test_attach_form_progress(raw, expected):
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "progress": raw})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["progress"] == expected


def test_attach_form_invalid_progress_invalid():
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "progress": "abc"})
    assert not form.is_valid()
    assert "progress" in form.errors


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param("", UserWorkStatusChoices.PLANNING, id="empty-default"),
        pytest.param(
            UserWorkStatusChoices.COMPLETED,
            UserWorkStatusChoices.COMPLETED,
            id="completed",
        ),
        pytest.param(
            UserWorkStatusChoices.DROPPED,
            UserWorkStatusChoices.DROPPED,
            id="dropped",
        ),
    ],
)
def test_attach_form_status(raw, expected):
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "status": raw})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["status"] == expected


def test_attach_form_unknown_status_invalid():
    form = AttachWorkForm(data={"work_type": "book", "work_id": "1", "status": "bogus"})
    assert not form.is_valid()
    assert "status" in form.errors
