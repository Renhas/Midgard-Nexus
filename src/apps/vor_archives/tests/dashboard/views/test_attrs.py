"""Tests for attrs tab in apps.vor_archives.dashboard."""

import pytest
from django.urls import reverse

from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db


def test_attrs_context_and_template_structure(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:dashboard:tab", kwargs={"tab": "attrs"})
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
    assert 'id="vor-dash-attrs-opts"' in content
    for view in ctx["view_types"]:
        assert f"setAttrView('{view['key']}')" in content
    for kind in ctx["attr_kinds"]:
        assert f'x-ref="cloud-{kind["key"]}"' in content
        assert f'x-ref="bar-{kind["key"]}"' in content
