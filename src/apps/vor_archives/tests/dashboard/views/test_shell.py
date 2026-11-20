"""Tests for apps.vor_archives.dashboard.views.shell."""

import pytest
from django.urls import reverse

from apps.vor_archives.dashboard.catalog import DASHBOARD_TABS
from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db

TAB_PARAMS = [(tab["kind"], tab["label"]) for tab in DASHBOARD_TABS]


def test_dashboard_requires_login(client):
    response = client.get(reverse("vor_archives:dashboard:index"))
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


def test_dashboard_redirects_to_stats(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:dashboard:index"))
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "vor_archives:dashboard:tab", kwargs={"tab": "stats"}
    )


def test_dashboard_tab_requires_login(client):
    response = client.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "stats"})
    )
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


@pytest.mark.parametrize("tab,label", TAB_PARAMS)
def test_dashboard_tabs_ok(client_logged_in, user, book, tab, label):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": tab})
    )
    assert response.status_code == 200
    ctx = response.context
    assert ctx["dash_kind"] == tab
    assert ctx["hide_right"] is True
    assert ctx["active_section"] == "dashboard"
    content = response.content.decode()
    assert label in content
    assert 'id="vor-overlay"' in content
    assert 'id="vor-modal"' in content


def test_dashboard_unknown_tab_404(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "unknown"})
    )
    assert response.status_code == 404


def test_dashboard_legacy_charts_tab_404(client_logged_in):
    """Регрессия: вкладка charts переименована в attrs."""
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "charts"})
    )
    assert response.status_code == 404
