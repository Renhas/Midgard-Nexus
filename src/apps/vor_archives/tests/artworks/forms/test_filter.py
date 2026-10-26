"""Tests for apps.vor_archives.artworks.forms.ArtworkListFilterForm."""

from urllib.parse import urlencode

import pytest
from django.test import RequestFactory

from apps.vor_archives.artworks.forms import ArtworkListFilterForm
from apps.vor_archives.constants import AgeRatingChoices, UserWorkStatusChoices
from apps.vor_archives.tests.factories import (
    BookGenreFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


def _form(query=""):
    request = RequestFactory().get(f"/{query}")
    return ArtworkListFilterForm(request.GET)


# ─── defaults ───────────────────────────────────────────────────────────────


def test_empty_query_yields_empty_filters():
    params = _form().to_service_params()
    assert params["types"] == []
    assert params["statuses"] == []
    assert params["age_ratings"] == []
    assert params["tags"] == []
    assert params["genre_book"] == []
    assert params["platforms"] == []
    assert params["sort"] == "custom"
    assert params["sort_asc"] is True
    assert params["show_hidden"] is True
    assert params["collection_id"] is None


# ─── types / status / age_rating ────────────────────────────────────────────


@pytest.mark.parametrize("type_key", ["book", "film", "game"])
def test_types_single(type_key):
    params = _form(f"?types={type_key}").to_service_params()
    assert params["types"] == [type_key]


def test_types_multiple():
    params = _form("?types=book&types=film").to_service_params()
    assert params["types"] == ["book", "film"]


def test_types_unknown_rejected_by_form():
    form = _form("?types=nope")
    assert not form.is_valid()
    assert "types" in form.errors


def test_status_single():
    params = _form(f"?status={UserWorkStatusChoices.PLANNING}").to_service_params()
    assert params["statuses"] == [UserWorkStatusChoices.PLANNING]


def test_status_unknown_rejected():
    form = _form("?status=bogus")
    assert not form.is_valid()
    assert "status" in form.errors


@pytest.mark.parametrize(
    "value",
    [
        AgeRatingChoices.RATING_0,
        AgeRatingChoices.RATING_12,
        AgeRatingChoices.RATING_18,
    ],
)
def test_age_rating_single(value):
    query = "?" + urlencode({"age_rating": value})
    params = _form(query).to_service_params()
    assert params["age_ratings"] == [value]


def test_age_rating_unknown_rejected():
    form = _form("?age_rating=99+")
    assert not form.is_valid()
    assert "age_rating" in form.errors


# ─── model-based filters ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_tags_resolved_to_pks():
    tag = TagFactory()
    params = _form(f"?tags={tag.pk}").to_service_params()
    assert params["tags"] == [tag.pk]


@pytest.mark.django_db
def test_tags_unknown_pk_rejected():
    form = _form("?tags=999999")
    assert not form.is_valid()
    assert "tags" in form.errors


@pytest.mark.django_db
def test_genre_book_resolved_to_pks():
    genre = BookGenreFactory()
    params = _form(f"?genre_book={genre.pk}").to_service_params()
    assert params["genre_book"] == [genre.pk]


@pytest.mark.django_db
def test_platform_resolved_to_pks():
    platform = PlatformFactory()
    params = _form(f"?platform={platform.pk}").to_service_params()
    assert params["platforms"] == [platform.pk]


# ─── all_* metadata ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_all_metadata_populated():
    tag = TagFactory()
    platform = PlatformFactory()

    params = _form().to_service_params()

    assert params["all_statuses"] == list(UserWorkStatusChoices.values)
    assert params["all_age_ratings"] == list(AgeRatingChoices.values)
    assert tag.pk in params["all_tags"]
    assert platform.pk in params["all_platforms"]


# ─── lenient non-filter fields ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "query,expected_asc",
    [
        pytest.param("", True, id="absent"),
        pytest.param("?dir=asc", True, id="asc"),
        pytest.param("?dir=desc", False, id="desc"),
        pytest.param("?dir=bogus", True, id="bogus-falls-back-asc"),
    ],
)
def test_sort_dir(query, expected_asc):
    params = _form(query).to_service_params()
    assert params["sort_asc"] is expected_asc


@pytest.mark.parametrize(
    "query,expected",
    [
        pytest.param("", True, id="absent"),
        pytest.param("?hidden=1", True, id="1"),
        pytest.param("?hidden=0", False, id="0"),
        pytest.param("?hidden=bogus", True, id="bogus-falls-back"),
    ],
)
def test_show_hidden(query, expected):
    params = _form(query).to_service_params()
    assert params["show_hidden"] is expected


@pytest.mark.parametrize(
    "query,expected",
    [
        pytest.param("", "custom", id="absent"),
        pytest.param("?sort=title", "title", id="valid"),
        pytest.param("?sort=bogus", "bogus", id="passthrough"),
    ],
)
def test_sort_field(query, expected):
    params = _form(query).to_service_params()
    assert params["sort"] == expected


@pytest.mark.parametrize(
    "query,expected",
    [
        pytest.param("", None, id="absent"),
        pytest.param("?collection=5", 5, id="valid"),
        pytest.param("?collection=bogus", None, id="invalid"),
    ],
)
def test_collection(query, expected):
    params = _form(query).to_service_params()
    assert params["collection_id"] == expected
