"""Playwright smoke tests: main pages render and respond."""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.django_db(transaction=True),
]


def test_home_renders_for_anonymous(live_server, page: Page):
    page.goto(live_server.url)
    expect(page).to_have_title(re.compile("Midgard Nexus"))
    expect(page.get_by_role("heading", name="Midgard Nexus")).to_be_visible()
    expect(page.get_by_text("Незнакомцам вход закрыт")).to_be_visible()


def test_home_renders_for_authenticated(live_server, authenticated_page):
    authenticated_page.goto(live_server.url)
    expect(authenticated_page).to_have_title(re.compile("Midgard Nexus"))
    expect(authenticated_page.get_by_text("Добро пожаловать")).to_be_visible()


def test_login_page_renders(live_server, page: Page):
    page.goto(f"{live_server.url}/users/login/")
    expect(page).to_have_title(re.compile("Вход"))
    expect(page.get_by_role("heading", name="Вход в систему")).to_be_visible()
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()
    expect(page.get_by_role("button", name="Войти")).to_be_visible()


def test_signup_page_renders(live_server, page: Page):
    page.goto(f"{live_server.url}/users/signup/")
    expect(page).to_have_title(re.compile("Регистрация"))
    expect(page.get_by_role("heading", name="Регистрация")).to_be_visible()
    expect(page.get_by_role("button", name="Зарегистрироваться")).to_be_visible()


def test_library_renders_seeded_works(live_server, authenticated_page, user_work):
    console_errors: list[str] = []
    failed_requests: list[str] = []
    page_errors: list[str] = []

    def _on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    authenticated_page.on("console", _on_console)
    authenticated_page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    authenticated_page.on(
        "requestfailed",
        lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"),
    )

    authenticated_page.goto(f"{live_server.url}/library/")
    expect(authenticated_page).to_have_title(re.compile("Произведения"))
    list_body = authenticated_page.locator("#artwork-list-body")
    try:
        expect(list_body.get_by_text("Загрузка…")).to_be_hidden(timeout=20_000)
    except AssertionError as exc:
        alpine_ok = authenticated_page.evaluate("typeof window.Alpine !== 'undefined'")
        htmx_ok = authenticated_page.evaluate("typeof window.htmx !== 'undefined'")
        raise AssertionError(
            "library list did not finish loading in time.\n"
            f"Alpine loaded: {alpine_ok}\n"
            f"HTMX loaded: {htmx_ok}\n"
            f"console errors: {console_errors or 'none'}\n"
            f"page errors: {page_errors or 'none'}\n"
            f"failed requests: {failed_requests or 'none'}"
        ) from exc
    expect(authenticated_page.get_by_text(user_work.work.title).first).to_be_visible()


def test_artwork_overlay_renders(live_server, authenticated_page, user_work):
    authenticated_page.goto(f"{live_server.url}/library/artworks/{user_work.pk}/")
    expect(
        authenticated_page.get_by_role("heading", name=user_work.work.title)
    ).to_be_visible()
    expect(authenticated_page.get_by_role("button", name="Назад").first).to_be_visible()


def test_attributes_renders(live_server, authenticated_page):
    authenticated_page.goto(f"{live_server.url}/library/attributes/")
    expect(authenticated_page).to_have_title(re.compile("рибут"))
    expect(authenticated_page).to_have_url(re.compile(r"/library/attributes/.+/"))
    expect(authenticated_page.locator('input[type="search"]')).to_be_visible()


def test_dashboard_renders(live_server, authenticated_page):
    authenticated_page.goto(f"{live_server.url}/library/dashboard/")
    expect(authenticated_page).to_have_title(re.compile("Дашборд"))
    expect(authenticated_page).to_have_url(re.compile(r"/library/dashboard/.+/"))
