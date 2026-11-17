"""E2E-specific setup for Playwright + Django sync ORM compatibility."""

import os

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.tests.factories import BookFactory, UserWorkFactory

# Playwright's sync API runs an asyncio event loop in a background thread.
# Django's ORM is synchronous, and accessing it from that thread without
# this flag raises SynchronousOnlyOperation. Scoped to e2e only.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def book():
    return BookFactory()


@pytest.fixture
def user_work(user, book):
    return UserWorkFactory(user=user, work=book)


@pytest.fixture
def authenticated_page(page, client, user, live_server):
    client.force_login(user)
    sessionid = client.cookies["sessionid"].value
    page.context.add_cookies(
        [{"name": "sessionid", "value": sessionid, "url": live_server.url}]
    )
    return page
