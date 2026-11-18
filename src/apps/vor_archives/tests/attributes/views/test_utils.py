"""Tests for apps.vor_archives.attributes.views.utils."""

import json

import pytest
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse

from apps.vor_archives.attributes.forms import AttrForm, GenreForm
from apps.vor_archives.attributes.views.utils import (
    attach_item_urls,
    attr_list_context,
    attr_mutation_response,
    attr_tab_or_404,
    empty_context,
    form_context,
    genre_item_context,
    require_staff,
    search_query,
    simple_item_context,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── require_staff & attr_tab_or_404 & search_query ─────────────────────────


def test_require_staff_blocks_regular_user_and_allows_staff(user, staff_user):
    rf = RequestFactory()

    req_user = rf.get("/")
    req_user.user = user
    forbidden = require_staff(req_user)
    assert forbidden is not None
    assert forbidden.status_code == 403

    req_staff = rf.get("/")
    req_staff.user = staff_user
    assert require_staff(req_staff) is None


def test_attr_tab_or_404():
    assert attr_tab_or_404("tags")["kind"] == "tags"
    with pytest.raises(Http404):
        attr_tab_or_404("unknown")


def test_search_query_reads_get_or_post():
    rf = RequestFactory()
    assert search_query(rf.get("/", {"q": "fantasy"})) == "fantasy"
    assert search_query(rf.post("/", {"q": "horror"})) == "horror"
    assert search_query(rf.get("/")) == ""


# ─── attach_item_urls ───────────────────────────────────────────────────────


def test_attach_item_urls_simple_and_genre():
    simple = attach_item_urls("tags", {"pk": 5})
    assert simple["detail_url"] == reverse(
        "vor_archives:attributes:detail", args=["tags", 5]
    )
    assert simple["edit_url"] == reverse(
        "vor_archives:attributes:edit", args=["tags", 5]
    )

    genre = attach_item_urls("genres", {"type_key": "book", "pk": 7})
    assert genre["detail_url"] == reverse(
        "vor_archives:attributes:genre_detail", args=["book", 7]
    )
    assert genre["edit_url"] == reverse(
        "vor_archives:attributes:genre_edit", args=["book", 7]
    )


# ─── attr_list_context, *_item_context, empty_context ───────────────────────


def test_attr_list_context_simple_and_genres(user):
    rf = RequestFactory()
    tag = TagFactory(name="Classic")
    genre = BookGenreFactory(name="Novel")

    req = rf.get("/")
    req.user = user

    simple_ctx = attr_list_context(req, "tags")
    assert simple_ctx["has_items"] is True
    assert simple_ctx["total_count"] == 1
    assert simple_ctx["groups"] == []
    assert simple_ctx["items"][0]["pk"] == tag.pk
    assert "detail_url" in simple_ctx["items"][0]

    genre_ctx = attr_list_context(req, "genres")
    assert genre_ctx["has_items"] is True
    assert genre_ctx["total_count"] == 1
    assert genre_ctx["items"] == []
    book_group = next(g for g in genre_ctx["groups"] if g["type_key"] == "book")
    assert book_group["items"][0]["pk"] == genre.pk
    assert "detail_url" in book_group["items"][0]


def test_item_contexts_and_empty_context(staff_user):
    rf = RequestFactory()
    req = rf.get("/")
    req.user = staff_user

    platform = PlatformFactory(name="PC")
    simple_ctx = simple_item_context(req, "platforms", platform)
    assert simple_ctx["item"]["has_text"] is False
    assert simple_ctx["item"]["description"] == ""
    assert simple_ctx["is_staff"] is True

    genre = BookGenreFactory(name="Fantasy", description="Magic")
    book = BookFactory()
    book.genres.add(genre)
    genre_ctx = genre_item_context(req, genre, "book")
    assert genre_ctx["item"]["key"] == f"book:{genre.pk}"
    assert genre_ctx["item"]["type_label"] == "Книги"
    assert genre_ctx["item"]["work_count"] == 1
    assert genre_ctx["item"]["has_text"] is True

    empty_ctx = empty_context("persons")
    assert empty_ctx["kind"] == "persons"
    assert empty_ctx["empty_prompt"] == empty_ctx["tab"]["empty_prompt"]


# ─── form_context & attr_mutation_response ──────────────────────────────────


def test_form_context_create_and_edit_urls():
    create_simple = form_context(
        "platforms", AttrForm(kind="platforms"), is_create=True
    )
    assert create_simple["has_text"] is False
    assert create_simple["show_type"] is False
    assert create_simple["save_url"] == reverse(
        "vor_archives:attributes:new", args=["platforms"]
    )
    assert create_simple["cancel_url"] == reverse(
        "vor_archives:attributes:empty", args=["platforms"]
    )

    edit_simple = form_context("tags", AttrForm(kind="tags"), is_create=False, pk=3)
    assert edit_simple["has_text"] is True
    assert edit_simple["save_url"] == reverse(
        "vor_archives:attributes:edit", args=["tags", 3]
    )
    assert edit_simple["cancel_url"] == reverse(
        "vor_archives:attributes:detail", args=["tags", 3]
    )

    edit_genre = form_context(
        "genres",
        GenreForm(initial_type="film", lock_type=True),
        is_create=False,
        type_key="film",
        pk=9,
        type_label="Фильмы",
        lock_type=True,
    )
    assert edit_genre["show_type"] is True
    assert edit_genre["lock_type"] is True
    assert edit_genre["save_url"] == reverse(
        "vor_archives:attributes:genre_edit", args=["film", 9]
    )
    assert edit_genre["cancel_url"] == reverse(
        "vor_archives:attributes:genre_detail", args=["film", 9]
    )


def test_attr_mutation_response_sets_hx_trigger(user):
    rf = RequestFactory()
    req = rf.post("/")
    req.user = user

    response = attr_mutation_response(
        req,
        "vor_archives/partials/attributes/attr_empty.html",
        empty_context("tags"),
        extra_trigger={"vor:close-attr-modal": True},
    )
    assert response.status_code == 200
    assert json.loads(response["HX-Trigger"]) == {
        "vor:attr-list-refresh": True,
        "vor:close-attr-modal": True,
    }
