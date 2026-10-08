"""Tests for apps.vor_archives dashboard views."""

import json
import re

import pytest
from django.urls import reverse

from apps.vor_archives.dashboard_catalog import DASHBOARD_TABS
from apps.vor_archives.tests.factories import (
    BookFactory,
    UserWorkFactory,
)


pytestmark = pytest.mark.django_db


TAB_PARAMS = [(tab["kind"], tab["label"]) for tab in DASHBOARD_TABS]


# ─── dashboard: редирект ────────────────────────────────────────────────────


def test_dashboard_requires_login(client):
    response = client.get(reverse("vor_archives:dashboard"))
    assert response.status_code == 302


def test_dashboard_redirects_to_stats(client, user):
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard"))
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "vor_archives:dashboard_tab", kwargs={"tab": "stats"}
    )


# ─── dashboard_tab: оболочка ────────────────────────────────────────────────


@pytest.mark.parametrize("tab,label", TAB_PARAMS)
def test_dashboard_tabs_ok(client, user, book, tab, label):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard_tab", kwargs={"tab": tab}))
    assert response.status_code == 200
    ctx = response.context
    assert ctx["dash_kind"] == tab
    assert ctx["hide_right"] is True
    assert ctx["active_section"] == "dashboard"
    content = response.content.decode()
    assert label in content
    # Контейнеры для HTMX-модалок есть на каждой вкладке
    assert 'id="vor-overlay"' in content
    assert 'id="vor-modal"' in content


def test_dashboard_unknown_tab_404(client, user):
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "unknown"})
    )
    assert response.status_code == 404


def test_dashboard_legacy_charts_tab_404(client, user):
    """Регрессия: вкладка charts переименована в attrs."""
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "charts"})
    )
    assert response.status_code == 404


# ─── stats ──────────────────────────────────────────────────────────────────


def test_stats_context_has_stats_opts(client, user, book):
    """Wiring: view прокидывает stats_opts в контекст шаблона."""
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "stats"})
    )
    assert response.status_code == 200
    assert "stats_opts" in response.context


def test_stats_json_payload_keys_match_js_contract(client, user, book):
    """Ключи, которые читает vorDashStats.init(), обязаны быть в payload."""
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "stats"})
    )
    payload = _extract_json_script(response.content.decode(), "dash-stats-opts")
    # зеркало vorDashStats.init()
    for key in (
        "status_matrix",
        "age_matrix",
        "rating_matrix",
        "spent",
        "type_meta",
        "status_choices",
        "age_choices",
        "rating_choices",
    ):
        assert key in payload, f"JS reads data.{key}, but it's missing"


def test_stats_template_has_all_canvases(client, user, book):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "stats"})
    )
    content = response.content.decode()
    assert 'x-data="vorDashStats()"' in content
    for ref in ("pieTypes", "pieAge", "pieRating", "barRating", "pieStatus"):
        assert f'x-ref="{ref}"' in content
    for kind in ("book", "film", "game"):
        assert f"toggleType('{kind}')" in content


# ─── attrs ──────────────────────────────────────────────────────────────────


def test_attrs_context_and_view_buttons(client, user, book):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "attrs"})
    )
    assert response.status_code == 200
    ctx = response.context

    assert [v["key"] for v in ctx["view_types"]] == ["cloud", "bar", "list"]
    assert [k["key"] for k in ctx["attr_kinds"]] == [
        "tags",
        "persons",
        "genres",
        "platforms",
    ]

    opts = ctx["attrs_opts"]
    assert set(opts["attrs"]) == {"tags", "genres", "persons", "platforms"}
    assert opts["histTopN"] == 12
    assert opts["total"] == 1

    content = response.content.decode()
    assert 'x-data="vorDashAttrs()"' in content
    assert 'id="dash-attrs-opts"' in content
    for view in ctx["view_types"]:
        assert f"setAttrView('{view['key']}')" in content
    for kind in ctx["attr_kinds"]:
        assert f'x-ref="cloud-{kind["key"]}"' in content
        assert f'x-ref="bar-{kind["key"]}"' in content


# ─── activity / feed / heatmap ──────────────────────────────────────────────


def test_activity_tab_contains_heatmap_and_feed(client, user, book):
    UserWorkFactory(user=user, work=book)  # сигнал создаст FeedItem(ADDED)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "activity"})
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
    assert reverse("vor_archives:dashboard_heatmap") in content


def test_activity_tab_year_filter(client, user, book):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "activity"}),
        {"year": "2024"},
    )
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] == 2024


def test_activity_tab_invalid_year_falls_back_to_none(client, user):
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "activity"}),
        {"year": "not-a-year"},
    )
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] is None


def test_dashboard_feed_partial_returns_items(client, user, book):
    UserWorkFactory(user=user, work=book)  # → FeedItem(ADDED)
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard_feed"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "dash-feed-item" in content
    assert book.title in content

    # Контракт HTMX-ссылки на карточку работы — без хардкода маршрута.
    item = response.context["feed_items"][0]
    assert item["detail_url"].startswith("/")
    assert 'hx-get="' in content
    assert 'hx-target="#vor-overlay"' in content


def test_dashboard_feed_pagination(client, user):
    """FEED_PAGE_SIZE=30: 31 работа → две страницы без пересечений."""
    for _ in range(31):
        UserWorkFactory(user=user, work=BookFactory())
    client.force_login(user)

    first = client.get(reverse("vor_archives:dashboard_feed"))
    assert first.status_code == 200
    assert first.context["feed_has_more"] is True
    assert first.context["feed_next_offset"] == 30

    second = client.get(
        reverse("vor_archives:dashboard_feed"),
        {"offset": first.context["feed_next_offset"]},
    )
    assert second.status_code == 200
    assert second.context["feed_has_more"] is False
    ids_first = {i["id"] for i in first.context["feed_items"]}
    ids_second = {i["id"] for i in second.context["feed_items"]}
    assert not (ids_first & ids_second)


def test_dashboard_feed_invalid_offset_falls_back_to_zero(client, user):
    client.force_login(user)
    for bad in ("abc", "-5", ""):
        response = client.get(reverse("vor_archives:dashboard_feed"), {"offset": bad})
        assert response.status_code == 200, bad


def test_dashboard_heatmap_partial_ok(client, user, book):
    """Wiring: view парсит ?year и прокидывает в шаблон partial."""
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard_heatmap"), {"year": "2024"})
    assert response.status_code == 200
    assert response.context["heatmap"]["year"] == 2024
    assert "dash-heatmap" in response.content.decode()


# ─── HTTP-методы, авторизация, изоляция ────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    ["vor_archives:dashboard_feed", "vor_archives:dashboard_heatmap"],
)
def test_partials_require_login(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 302


def test_feed_and_heatmap_require_get(client, user):
    client.force_login(user)
    for name in ("vor_archives:dashboard_feed", "vor_archives:dashboard_heatmap"):
        response = client.post(reverse(name))
        assert response.status_code == 405, name


# ─── helper ─────────────────────────────────────────────────────────────────


def _extract_json_script(html: str, element_id: str):
    """Достаёт JSON из <script id="..." type="application/json">…</script>."""
    m = re.search(
        rf'<script id="{re.escape(element_id)}" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert m, f"json_script #{element_id} not found"
    return json.loads(m.group(1))
