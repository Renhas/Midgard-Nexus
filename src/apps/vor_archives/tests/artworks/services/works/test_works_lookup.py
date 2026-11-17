"""Tests for apps.vor_archives.artworks.services.works - lookups.

Covers get_work_model, get_work, work_type_key, get_user_work,
user_has_work and user_owned_work_ids.
"""

import pytest
from django.http import Http404

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    get_user_work,
    get_work,
    user_has_work,
    user_owned_work_ids,
    work_type_key,
)
from apps.vor_archives.artworks.services.works import get_work_model
from apps.vor_archives.models import (
    Book,
    Film,
    Game,
)
from apps.vor_archives.tests.factories import UserWorkFactory


# ─── get_work_model / get_work / work_type_key ──────────────────────────────


def test_get_work_model_returns_correct_classes():
    assert get_work_model("book") is Book
    assert get_work_model("film") is Film
    assert get_work_model("game") is Game


def test_get_work_model_raises_for_unknown():
    with pytest.raises(ValueError):
        get_work_model("nope")


@pytest.mark.django_db
def test_get_work_returns_object(book):
    assert get_work("book", book.pk) == book


@pytest.mark.django_db
def test_get_work_raises_404_for_missing():
    with pytest.raises(Http404):
        get_work("book", 999999)


def test_get_work_raises_value_error_for_unknown_type():
    with pytest.raises(ValueError):
        get_work("nope", 1)


@pytest.mark.django_db
def test_work_type_key(book, movie, game):
    assert work_type_key(book) == "book"
    assert work_type_key(movie) == "film"
    assert work_type_key(game) == "game"


# ─── get_user_work / user_has_work / user_owned_work_ids ─────────────────────


@pytest.mark.django_db
def test_get_user_work_returns_owned(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert get_user_work(user, book) == uw


@pytest.mark.django_db
def test_get_user_work_returns_none_when_not_owned(user, book):
    assert get_user_work(user, book) is None


@pytest.mark.django_db
def test_get_user_work_ignores_other_users(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    assert get_user_work(user, book) is None


@pytest.mark.django_db
def test_user_has_work(user, book):
    assert user_has_work(user, book) is False
    UserWorkFactory(user=user, work=book)
    assert user_has_work(user, book) is True


@pytest.mark.django_db
def test_user_owned_work_ids(user, book, movie):
    UserWorkFactory(user=user, work=book)

    assert list(user_owned_work_ids(user, "book")) == [book.pk]
    assert list(user_owned_work_ids(user, "film")) == []


@pytest.mark.django_db
def test_user_owned_work_ids_ignores_other_users(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    assert list(user_owned_work_ids(user, "book")) == []
