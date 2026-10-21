"""Tests for apps.vor_archives.artworks.services.utils."""

from types import SimpleNamespace

from apps.vor_archives.artworks.services.utils import (
    is_partial,
    item_ids,
    relation_cover_url,
    work_key,
)
from ...conftest import ALL_STATUSES

# ─── work_key ────────────────────────────────────────────────────────────────


def test_work_key_uses_content_type_and_object_id():
    obj = SimpleNamespace(work_content_type_id=5, work_object_id=42)
    assert work_key(obj) == (5, 42)


# ─── relation_cover_url ──────────────────────────────────────────────────────


def test_relation_cover_url_returns_empty_when_cover_missing():
    obj = SimpleNamespace(cover=None)
    assert relation_cover_url(obj) == ""


def test_relation_cover_url_returns_empty_when_cover_falsy():
    obj = SimpleNamespace(cover="")
    assert relation_cover_url(obj) == ""


def test_relation_cover_url_returns_empty_when_work_has_no_cover_attr():
    obj = SimpleNamespace()
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


def test_is_partial_returns_false_when_all_values_empty():
    assert is_partial([1, 2], []) is False


def test_is_partial_returns_false_when_all_values_none():
    assert is_partial([1, 2], None) is False


def test_is_partial_returns_false_when_selection_matches_all():
    assert is_partial([1, 2], [1, 2]) is False
    assert is_partial([1, 2], [2, 1]) is False


def test_is_partial_normalizes_to_strings():
    assert is_partial(["1", "2"], [1, 2]) is False
    assert is_partial([1, 2], ["1", "2"]) is False


def test_is_partial_returns_true_for_subset():
    assert is_partial([1], [1, 2]) is True


def test_is_partial_returns_true_for_superset():
    assert is_partial([1, 2, 3], [1, 2]) is True


def test_is_partial_returns_true_when_selection_empty():
    assert is_partial([], [1, 2]) is True


def test_is_partial_returns_true_when_selection_none():
    assert is_partial(None, [1, 2]) is True


# ─── item_ids ────────────────────────────────────────────────────────────────


def test_item_ids_returns_set_of_pks():
    items = [SimpleNamespace(pk=1), SimpleNamespace(pk=2)]
    assert item_ids(items) == {1, 2}


def test_item_ids_empty_list():
    assert item_ids([]) == set()
