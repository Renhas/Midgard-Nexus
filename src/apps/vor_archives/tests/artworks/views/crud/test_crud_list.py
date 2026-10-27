"""Tests for artwork_list view: library listing with filters and collections."""

import pytest
from django.urls import reverse

from apps.vor_archives.registry import WORK_MODELS
from apps.vor_archives.constants import (
    AgeRatingChoices,
    UserWorkStatusChoices,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    GameFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


ALL_STATUSES = list(UserWorkStatusChoices.values)
ALL_AGE_RATINGS = list(AgeRatingChoices.values)
ALL_TYPES = list(WORK_MODELS.keys())


def _filters(**overrides):
    params = {
        "types": ALL_TYPES,
        "status": ALL_STATUSES,
        "age_rating": ALL_AGE_RATINGS,
    }
    params.update(overrides)
    return params


# ─── artwork_list ───────────────────────────────────────────────────────────


def test_list_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:list"))
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


def test_list_ok(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(reverse("vor_archives:artworks:list"), _filters())
    assert response.status_code == 200
    assert response.context["collection"] is None
    assert len(response.context["user_works"]) == 1


def test_list_filters_by_type(client_logged_in, user, book, movie):
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"), _filters(types="book")
    )
    assert response.status_code == 200
    assert len(response.context["user_works"]) == 1


def test_list_with_collection_id_uses_segments(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    CollectionItemFactory(collection=collection, work=book)
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(collection=collection.pk, types="book"),
    )
    assert response.status_code == 200
    assert response.context["collection"] == collection
    assert len(response.context["direct"]) == 1
    assert response.context["user_works"] == []


def test_list_empty_without_age_rating_param(client_logged_in, user, book):
    """Documents current behavior: absent age_rating query filters everything out.

    The view always sends all_age_ratings as a non-empty list of AgeRatingChoices,
    but age_ratings defaults to []. Any work whose age_rating is "" (the model
    default) is then excluded. The frontend sends all age ratings on load, so
    this is only reachable via a direct URL call. Same class of issue as with
    statuses: types has a fallback to all when absent, but per-checkbox filters
    do not.
    """
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        {"types": ALL_TYPES, "status": ALL_STATUSES},
    )
    assert response.status_code == 200
    assert response.context["user_works"] == []


def test_list_empty_without_types(client_logged_in, user, book):
    """Missing types now yields an empty list, matching every other filter."""
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(reverse("vor_archives:artworks:list"))
    assert response.status_code == 200
    assert response.context["user_works"] == []


def test_list_foreign_collection_404(client_logged_in):
    other = UserFactory()
    foreign_collection = CollectionFactory(user=other)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        {"collection": foreign_collection.pk},
    )
    assert response.status_code == 404


def test_list_get_only(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:list"))
    assert response.status_code == 405


def test_list_invalid_filter_value_returns_empty(client_logged_in, user, book):
    """Invalid filter values fall back to an empty form -> empty list."""
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        {"types": ALL_TYPES, "status": "bogus"},
    )
    assert response.status_code == 200
    assert response.context["user_works"] == []


# ─── artwork_list: filter query params ──────────────────────────────────────


def test_list_filter_by_tags(client_logged_in, user):
    tag1 = TagFactory()
    tag2 = TagFactory()
    book1 = BookFactory()
    book1.tags.add(tag1)
    book2 = BookFactory()
    book2.tags.add(tag2)
    UserWorkFactory(user=user, work=book1)
    UserWorkFactory(user=user, work=book2)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(tags=tag1.pk),
    )
    assert response.status_code == 200
    works = response.context["user_works"]
    assert len(works) == 1
    assert works[0].work_object_id == book1.pk


def test_list_filter_by_platform(client_logged_in, user):
    p1 = PlatformFactory()
    p2 = PlatformFactory()
    game1 = GameFactory()
    game1.platforms.add(p1)
    game2 = GameFactory()
    game2.platforms.add(p2)
    UserWorkFactory(user=user, work=game1)
    UserWorkFactory(user=user, work=game2)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(types="game", platform=p1.pk),
    )
    assert response.status_code == 200
    works = response.context["user_works"]
    assert len(works) == 1
    assert works[0].work_object_id == game1.pk
