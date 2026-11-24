"""Playwright e2e tests for artwork add overlay."""

import pytest
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_add_overlay_accordions_exclusive_and_relations_visible(
    live_server, authenticated_page
):
    authenticated_page.set_viewport_size({"width": 1280, "height": 720})
    authenticated_page.goto(f"{live_server.url}/library/")

    add_button = authenticated_page.locator(".sidebar-btn--add").first
    add_button.click()

    overlay = authenticated_page.locator(".vor-overlay--add")
    expect(overlay).to_be_visible()

    authors_btn = overlay.get_by_role("button", name="Авторы")
    genres_btn = overlay.get_by_role("button", name="Жанры")
    tags_btn = overlay.get_by_role("button", name="Теги")
    relations_panel = overlay.locator(".vor-add-relations")

    authors_body = overlay.locator("#attr-body-authors")
    genres_body = overlay.locator("#attr-body-genres")
    tags_body = overlay.locator("#attr-body-tags")

    authors_btn.click()
    expect(authors_body).to_be_visible()
    expect(genres_body).to_be_hidden()
    expect(tags_body).to_be_hidden()
    expect(relations_panel).to_be_in_viewport()

    genres_btn.click()
    expect(authors_body).to_be_hidden()
    expect(genres_body).to_be_visible()
    expect(tags_body).to_be_hidden()
    expect(relations_panel).to_be_in_viewport()

    tags_btn.click()
    expect(authors_body).to_be_hidden()
    expect(genres_body).to_be_hidden()
    expect(tags_body).to_be_visible()
    expect(relations_panel).to_be_in_viewport()

    has_vertical_scroll = overlay.evaluate("el => el.scrollHeight > el.clientHeight")
    assert not has_vertical_scroll

    # Closing the active accordion collapses all attribute panels
    tags_btn.click()
    expect(tags_body).to_be_hidden()
