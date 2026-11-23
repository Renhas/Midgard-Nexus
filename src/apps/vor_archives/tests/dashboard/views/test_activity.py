"""Tests for activity tab and partials in apps.vor_archives.dashboard.views.activity."""

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import BookFactory, UserWorkFactory

pytestmark = pytest.mark.django_db


# ─── Вкладка activity ───────────────────────────────────────────────────────


def test_activity_tab_contains_heatmap_and_feed(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "activity"})
    )
    assert response.status_code == 200
    ctx = response.context
    assert "feed_items" in ctx
    assert "feed_has_more" in ctx
    assert "feed_next_offset" in ctx
    assert "heatmap" in ctx

    content = response.content.decode()
    assert 'id="dash-heatmap"' in content
    assert 'id="dash-feed-list"' in content
    assert reverse("vor_archives:dashboard:heatmap") in content


def test_activity_tab_year_filter(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "activity"}),
        {"year": "2024"},
    )
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] == 2024


def test_activity_tab_invalid_year_falls_back_to_none(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "activity"}),
        {"year": "not-a-year"},
    )
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] is None


# ─── Авторизация и HTTP-методы партиалов ────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    ["vor_archives:dashboard:feed", "vor_archives:dashboard:heatmap"],
)
def test_partials_require_login(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


@pytest.mark.parametrize(
    "name",
    ["vor_archives:dashboard:feed", "vor_archives:dashboard:heatmap"],
)
def test_partials_require_get(client_logged_in, name):
    response = client_logged_in.post(reverse(name))
    assert response.status_code == 405


# ─── dashboard_feed ─────────────────────────────────────────────────────────


def test_dashboard_feed_partial_returns_items(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(reverse("vor_archives:dashboard:feed"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "dash-feed-item" in content
    assert book.title in content

    item = response.context["feed_items"][0]
    assert item["detail_url"].startswith("/")
    assert 'hx-get="' in content
    assert 'hx-target="#vor-overlay"' in content


def test_dashboard_feed_pagination_and_exact_page_boundary(client_logged_in, user):
    for _ in range(15):
        UserWorkFactory(user=user, work=BookFactory())

    exact_page = client_logged_in.get(reverse("vor_archives:dashboard:feed"))
    assert exact_page.status_code == 200
    assert exact_page.context["feed_has_more"] is False
    assert exact_page.context["feed_next_offset"] == 30

    UserWorkFactory(user=user, work=BookFactory())

    first = client_logged_in.get(reverse("vor_archives:dashboard:feed"))
    assert first.status_code == 200
    assert first.context["feed_has_more"] is True
    assert first.context["feed_next_offset"] == 30

    second = client_logged_in.get(
        reverse("vor_archives:dashboard:feed"),
        {"offset": first.context["feed_next_offset"]},
    )
    assert second.status_code == 200
    assert second.context["feed_has_more"] is False
    ids_first = {i["id"] for i in first.context["feed_items"]}
    ids_second = {i["id"] for i in second.context["feed_items"]}
    assert not (ids_first & ids_second)


@pytest.mark.parametrize("bad_offset", ["abc", "-5", "1.5", ""])
def test_dashboard_feed_invalid_offset_falls_back_to_zero(
    client_logged_in, user, book, bad_offset
):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:feed"), {"offset": bad_offset}
    )
    assert response.status_code == 200
    assert len(response.context["feed_items"]) == 2


def test_dashboard_feed_isolates_other_user(client_logged_in, other_user, book):
    UserWorkFactory(user=other_user, work=book)
    response = client_logged_in.get(reverse("vor_archives:dashboard:feed"))
    assert response.status_code == 200
    assert response.context["feed_items"] == []
    assert book.title not in response.content.decode()


# ─── dashboard_heatmap ──────────────────────────────────────────────────────


def test_dashboard_heatmap_partial_ok(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:heatmap"), {"year": "2024"}
    )
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] == 2024
    assert "dash-heatmap" in response.content.decode()


def test_dashboard_heatmap_isolates_other_user(client_logged_in, other_user, book):
    UserWorkFactory(user=other_user, work=book)
    response = client_logged_in.get(reverse("vor_archives:dashboard:heatmap"))
    assert response.status_code == 200
    assert response.context["heatmap"]["max_count"] == 0
