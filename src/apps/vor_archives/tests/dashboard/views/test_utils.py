"""Tests for apps.vor_archives.dashboard.views.utils and catalog helpers."""

import pytest
from django.http import Http404
from django.test import RequestFactory

from apps.vor_archives.dashboard.catalog import get_dash_tab
from apps.vor_archives.dashboard.views.utils import (
    dash_tab_or_404,
    render_dashboard_shell,
)

pytestmark = pytest.mark.django_db


def test_get_dash_tab():
    tab = get_dash_tab("stats")
    assert tab is not None
    assert tab["kind"] == "stats"
    assert get_dash_tab("unknown") is None


def test_dash_tab_or_404():
    assert dash_tab_or_404("attrs")["kind"] == "attrs"
    with pytest.raises(Http404):
        dash_tab_or_404("unknown")


def test_render_dashboard_shell_merges_context(user):
    rf = RequestFactory()
    request = rf.get("/vor/dashboard/stats/")
    request.user = user

    response = render_dashboard_shell(
        request,
        "stats",
        extra={"stats_opts": {"custom": 1}},
    )
    assert response.status_code == 200
    assert (
        b"stats_opts" not in response.content or b"dash-stats-opts" in response.content
    )
