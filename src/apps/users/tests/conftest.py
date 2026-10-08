"""Fixtures for apps.users tests."""

import pytest

from apps.users.tests.factories import UserFactory


@pytest.fixture
def user():
    return UserFactory()
