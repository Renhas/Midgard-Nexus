"""Fixtures for apps.vor_archives tests."""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.tests.factories import BookFactory, FilmFactory, GameFactory
from apps.vor_archives.constants import UserWorkStatusChoices

ALL_STATUSES = list(UserWorkStatusChoices.values)


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def other_user():
    return UserFactory()


@pytest.fixture
def admin_user():
    return UserFactory(username="admin", is_superuser=True, is_staff=True)


@pytest.fixture
def book():
    return BookFactory()


@pytest.fixture
def movie():
    return FilmFactory()


@pytest.fixture
def tv_show():
    return FilmFactory(tv=True)


@pytest.fixture
def game():
    return GameFactory()
