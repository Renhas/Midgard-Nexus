"""Playwright smoke test: app boots, serves HTML, browser renders it."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.smoke
@pytest.mark.django_db(transaction=True)
def test_app_responds_and_renders(live_server, page: Page):
    page.goto(live_server.url)
    expect(page.locator("body")).to_be_visible()
    assert page.title(), "rendered page must have a non-empty <title>"
