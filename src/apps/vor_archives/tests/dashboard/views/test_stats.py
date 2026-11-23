"""Tests for stats tab in apps.vor_archives.dashboard."""

import json
import re

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db


def _extract_json_script(html: str, element_id: str):
    match = re.search(
        rf'<script id="{re.escape(element_id)}" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match, f"json_script #{element_id} not found"
    return json.loads(match.group(1))


def test_stats_context_has_stats_opts(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "stats"})
    )
    assert response.status_code == 200
    assert "stats_opts" in response.context


def test_stats_json_payload_keys_match_js_contract(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "stats"})
    )
    payload = _extract_json_script(response.content.decode(), "vor-dash-stats-opts")
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


def test_stats_template_has_all_canvases_and_filters(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "stats"})
    )
    content = response.content.decode()
    assert 'x-data="vorDashStats()"' in content
    for ref in ("pieTypes", "pieAge", "pieRating", "barRating", "pieStatus"):
        assert f'x-ref="{ref}"' in content
    for kind in ("book", "film", "game"):
        assert f"toggleType('{kind}')" in content
