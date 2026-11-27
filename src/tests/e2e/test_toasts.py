import re

from playwright.sync_api import expect


def test_toast_stack_lifecycle_and_actions(authenticated_page, live_server):
    page = authenticated_page
    page.goto(f"{live_server.url}/library/")

    page.get_by_title("Добавить коллекцию").click()
    page.locator("#vor-modal input[name='name']").fill("Фантастика")
    page.locator("#vor-modal button[type='submit']").click()

    toast = page.locator(".app-toast.app-toast--success").first
    expect(toast).to_be_visible()
    expect(toast.locator(".app-toast__title")).not_to_be_empty()
    expect(toast.locator(".app-toast__message")).to_have_text("Фантастика")

    toast.locator(".app-toast__action-btn").click()
    expect(page.locator(".vor-artwork-library__path-link--current")).to_have_text(
        "Фантастика"
    )


def test_toast_stack_expand_and_dismiss_all(authenticated_page, live_server):
    page = authenticated_page
    page.goto(f"{live_server.url}/library/")

    page.evaluate(
        """() => {
            window.Alpine.store('toasts').show({ level: 'info', title: 'First', duration: 0 });
            window.Alpine.store('toasts').show({ level: 'success', title: 'Second', duration: 0 });
            window.Alpine.store('toasts').show({ level: 'error', title: 'Third', duration: 0 });
        }"""
    )

    viewport = page.locator(".app-toast-viewport")
    expect(viewport.locator(".app-toast")).to_have_count(3)

    viewport.hover()
    expect(viewport).to_have_class(re.compile(r"app-toast-viewport--expanded"))

    clear_all = viewport.locator(".app-toast-clear-all")
    expect(clear_all).to_be_visible()
    clear_all.click()

    expect(viewport.locator(".app-toast")).to_have_count(0)
