"""Tests for apps.vor_archives.artworks.services.utils."""

from types import SimpleNamespace

import pytest

from apps.vor_archives.artworks.services.utils import (
    is_partial,
    item_ids,
    relation_cover_url,
    work_key,
    optional_int,
)

# ─── work_key ────────────────────────────────────────────────────────────────


def test_work_key_uses_content_type_and_object_id():
    obj = SimpleNamespace(work_content_type_id=5, work_object_id=42)
    assert work_key(obj) == (5, 42)


# ─── relation_cover_url ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "obj",
    [
        pytest.param(SimpleNamespace(cover=None), id="cover-none"),
        pytest.param(SimpleNamespace(cover=""), id="cover-empty"),
        pytest.param(SimpleNamespace(), id="no-cover-attr"),
    ],
)
def test_relation_cover_url_returns_empty(obj):
    assert relation_cover_url(obj) == ""


def test_relation_cover_url_returns_url():
    cover = SimpleNamespace(url="/media/covers/x.jpg")
    obj = SimpleNamespace(cover=cover)
    assert relation_cover_url(obj) == "/media/covers/x.jpg"


def test_relation_cover_url_returns_empty_on_value_error():
    class Cover:
        def __bool__(self):
            return True

        @property
        def url(self):
            raise ValueError("no file")

    obj = SimpleNamespace(cover=Cover())
    assert relation_cover_url(obj) == ""


# ─── is_partial ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "selected,all_values,expected",
    [
        pytest.param([1, 2], [], False, id="all-empty-list"),
        pytest.param([1, 2], None, False, id="all-none"),
        pytest.param([1, 2], [1, 2], False, id="match-same-order"),
        pytest.param([1, 2], [2, 1], False, id="match-different-order"),
        pytest.param(["1", "2"], [1, 2], False, id="match-str-vs-int"),
        pytest.param([1], [1, 2], True, id="subset"),
        pytest.param([1, 2, 3], [1, 2], True, id="superset"),
        pytest.param([], [1, 2], True, id="selection-empty"),
        pytest.param(None, [1, 2], True, id="selection-none"),
    ],
)
def test_is_partial(selected, all_values, expected):
    assert is_partial(selected, all_values) is expected


# ─── item_ids ────────────────────────────────────────────────────────────────


def test_item_ids_returns_set_of_pks():
    items = [SimpleNamespace(pk=1), SimpleNamespace(pk=2)]
    assert item_ids(items) == {1, 2}


def test_item_ids_empty_list():
    assert item_ids([]) == set()


# ─── optional_int ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("42", 42, id="str-int"),
        pytest.param(42, 42, id="int"),
        pytest.param("  -7 ", -7, id="str-int-with-spaces"),
        pytest.param("0", 0, id="zero"),
        pytest.param(None, None, id="none"),
        pytest.param("", None, id="empty-string"),
        pytest.param("abc", None, id="non-numeric"),
        pytest.param("5.5", None, id="float-string"),
        pytest.param([], None, id="list"),
        pytest.param({}, None, id="dict"),
    ],
)
def test_optional_int(value, expected):
    assert optional_int(value) == expected
