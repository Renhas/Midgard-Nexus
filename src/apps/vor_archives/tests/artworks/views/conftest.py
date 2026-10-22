"""Fixtures for artworks views tests."""

import pytest

from apps.users.tests.factories import UserFactory


@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def staff_user():
    return UserFactory(is_staff=True)


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client
