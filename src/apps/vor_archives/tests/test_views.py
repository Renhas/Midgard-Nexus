"""Tests for apps.vor_archives dashboard views."""

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import UserWorkFactory


@pytest.mark.django_db
def test_dashboard_redirects_to_stats(client, user):
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard"))
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "vor_archives:dashboard_tab", kwargs={"tab": "stats"}
    )


@pytest.mark.django_db
@pytest.mark.parametrize("tab", ["stats", "charts", "activity"])
def test_dashboard_tabs_ok(client, user, book, tab):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(reverse("vor_archives:dashboard_tab", kwargs={"tab": tab}))
    assert response.status_code == 200
    assert response.context["dash_kind"] == tab
    assert response.context["hide_right"] is True
    content = response.content.decode()
    assert "Статистика" in content
    assert "Графики" in content
    assert "Активность" in content


@pytest.mark.django_db
def test_dashboard_unknown_tab_404(client, user):
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "unknown"})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_dashboard_stats_contains_kpi_and_type_cards(client, user, book):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    response = client.get(
        reverse("vor_archives:dashboard_tab", kwargs={"tab": "stats"})
    )
    assert response.context["total"] == 1
    assert response.context["type_cards"][0]["key"] == "book"
    assert "Всего" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_feed_and_heatmap_partials(client, user, book):
    UserWorkFactory(user=user, work=book)
    client.force_login(user)
    feed = client.get(reverse("vor_archives:dashboard_feed"))
    heat = client.get(reverse("vor_archives:dashboard_heatmap"), {"year": "2024"})
    assert feed.status_code == 200
    assert book.title in feed.content.decode()
    assert heat.status_code == 200
    assert "dash-heatmap" in heat.content.decode()
