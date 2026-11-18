"""Tests for apps.vor_archives.attributes.views.shell."""

import pytest
from django.urls import reverse

from apps.vor_archives.attributes.catalog import ATTR_TABS, DEFAULT_KIND

pytestmark = pytest.mark.django_db


def test_attributes_index_requires_login(client):
    response = client.get(reverse("vor_archives:attributes:index"))
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


def test_attributes_index_redirects_to_default_kind(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:attributes:index"))
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "vor_archives:attributes:kind", args=[DEFAULT_KIND]
    )


@pytest.mark.parametrize("tab", ATTR_TABS, ids=[t["kind"] for t in ATTR_TABS])
def test_attributes_kind_renders_tabs(client_logged_in, tab):
    response = client_logged_in.get(
        reverse("vor_archives:attributes:kind", args=[tab["kind"]])
    )
    assert response.status_code == 200
    assert response.context["attr_kind"] == tab["kind"]
    assert response.context["active_section"] == "attributes"
    assert response.context["hide_right"] is True
    assert response.context["is_staff"] is False


def test_attributes_kind_exposes_is_staff_for_staff_user(staff_client):
    response = staff_client.get(reverse("vor_archives:attributes:kind", args=["tags"]))
    assert response.status_code == 200
    assert response.context["is_staff"] is True


def test_attributes_kind_unknown_returns_404(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:attributes:kind", args=["unknown"])
    )
    assert response.status_code == 404
