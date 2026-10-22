"""Tests for apps.vor_archives.artworks.views.crud."""

import json

import pytest
from django.urls import reverse

from apps.vor_archives.constants import UserWorkStatusChoices, AgeRatingChoices
from apps.vor_archives.models import Book, Film, UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    UserWorkFactory,
    UserFactory,
)

ALL_STATUSES = list(UserWorkStatusChoices.values)
ALL_AGE_RATINGS = list(AgeRatingChoices.values)

pytestmark = pytest.mark.django_db


def _filters(**overrides):
    """Emulate the frontend: all filter checkboxes selected on load."""
    params = {
        "status": ALL_STATUSES,
        "age_rating": ALL_AGE_RATINGS,
    }
    params.update(overrides)
    return params


# ─── artwork_list ───────────────────────────────────────────────────────────


def test_list_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:list"))
    assert response.status_code == 302
    assert reverse("users:login") in response["Location"]


def test_list_ok(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(reverse("vor_archives:artworks:list"), _filters())
    assert response.status_code == 200
    assert response.context["collection"] is None
    assert len(response.context["user_works"]) == 1


def test_list_filters_by_type(client_logged_in, user, book, movie):
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"), _filters(types="book")
    )
    assert response.status_code == 200
    assert len(response.context["user_works"]) == 1


def test_list_with_collection_id_uses_segments(client_logged_in, user, book):
    collection = CollectionFactory(user=user)
    CollectionItemFactory(collection=collection, work=book)
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(collection=collection.pk, types="book"),
    )
    assert response.status_code == 200
    assert response.context["collection"] == collection
    assert len(response.context["direct"]) == 1
    assert response.context["user_works"] == []


def test_list_empty_without_age_rating_param(client_logged_in, user, book):
    """Documents current behavior: absent age_rating query filters everything out.

    The view always sends all_age_ratings as a non-empty list of AgeRatingChoices,
    but age_ratings defaults to []. Any work whose age_rating is "" (the model
    default) is then excluded. The frontend sends all age ratings on load, so
    this is only reachable via a direct URL call. Same class of issue as with
    statuses: types has a fallback to all when absent, but per-checkbox filters
    do not.
    """
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"), {"status": ALL_STATUSES}
    )
    assert response.status_code == 200
    assert response.context["user_works"] == []


def test_list_foreign_collection_404(client_logged_in):
    other = UserFactory()
    foreign_collection = CollectionFactory(user=other)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        {"collection": foreign_collection.pk},
    )
    assert response.status_code == 404


def test_list_get_only(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:list"))
    assert response.status_code == 405


# ─── artwork_add ────────────────────────────────────────────────────────────


def test_add_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:add"))
    assert response.status_code == 302


def test_add_get_context(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:add"))
    assert response.status_code == 200
    add_opts = response.context["add_opts"]
    assert add_opts["workType"] == "book"
    assert "saveUrl" in add_opts
    assert "searchUrl" in add_opts
    assert "previewUrl" in add_opts
    assert "attachUrl" in add_opts
    assert "listUrl" in add_opts
    assert "relationSearchUrl" in add_opts
    assert "relationTypes" in add_opts
    assert "catalogs" in add_opts
    assert "ageChoices" in add_opts
    assert "statusChoices" in add_opts


def test_add_post_unknown_type_400(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"), {"work_type": "nope"}
    )
    assert response.status_code == 400


def test_add_post_valid_book_creates_work(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "book", "title": "New Book", "pages": "100"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["work_type"] == "book"
    assert payload["title"] == "New Book"
    assert payload["progressMax"] == 100
    assert payload["progressUnit"] == "стр."
    assert payload["progressStep"] == 1
    assert Book.objects.filter(pk=payload["work_id"]).exists()


def test_add_post_invalid_book_returns_form_errors(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "book", "title": "", "pages": ""},
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False
    assert "title" in payload["errors"]
    assert "pages" in payload["errors"]


def test_add_post_movie_form_clears_episode_count(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "film",
            "title": "New Movie",
            "duration_minutes": "120",
            "film_type": "movie",
            "episode_count": "5",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)

    film = Film.objects.get(pk=payload["work_id"])
    assert film.episode_count is None


# ─── artwork_detail ─────────────────────────────────────────────────────────


def test_detail_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:detail", args=[1]))
    assert response.status_code == 302


def test_detail_foreign_uw_404(client_logged_in):
    other = UserFactory()
    uw = UserWorkFactory(user=other, work=BookFactory())
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 404


def test_detail_missing_uw_404(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[999999])
    )
    assert response.status_code == 404


def test_detail_get_ok(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    assert response.context["work"] == book
    assert response.context["owned"] is True
    assert response.context["user_work"] == uw


def test_detail_get_dangling_work_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    UserWork.objects.filter(pk=uw.pk).update(work_object_id=999999)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 400


def test_detail_get_edit_flag_ignored_for_non_staff(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk]), {"edit": "1"}
    )
    assert response.status_code == 200
    assert response.context["editing"] is False


def test_detail_get_edit_flag_for_staff(staff_client, staff_user, book):
    uw = UserWorkFactory(user=staff_user, work=book)
    response = staff_client.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk]), {"edit": "1"}
    )
    assert response.status_code == 200
    assert response.context["editing"] is True
    assert response.context["global_edit"] is True


def test_detail_post_non_staff_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:detail", args=[uw.pk]), {"title": "Hacked"}
    )
    assert response.status_code == 400


def test_detail_post_staff_updates_work(staff_client, staff_user):
    book = BookFactory(title="Old")
    UserWorkFactory(user=staff_user, work=book)
    response = staff_client.post(
        reverse("vor_archives:artworks:detail", args=[book.user_works.first().pk]),
        {"title": "Updated", "pages": "300"},
    )
    assert response.status_code == 200
    book.refresh_from_db()
    assert book.title == "Updated"
    assert "HX-Trigger" in response
    trigger = json.loads(response["HX-Trigger"])
    assert trigger.get("vor:reload-list") is True


def test_detail_post_staff_invalid_form_renders_errors(staff_client, staff_user):
    book = BookFactory(title="Old")
    uw = UserWorkFactory(user=staff_user, work=book)
    response = staff_client.post(
        reverse("vor_archives:artworks:detail", args=[uw.pk]),
        {"title": "", "pages": ""},
    )
    assert response.status_code == 200
    assert response.context["editing"] is True
    book.refresh_from_db()
    assert book.title == "Old"


# ─── artwork_work ───────────────────────────────────────────────────────────


def test_work_requires_login(client, book):
    response = client.get(reverse("vor_archives:artworks:work", args=["book", book.pk]))
    assert response.status_code == 302


def test_work_unknown_type_400(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:work", args=["nope", 1])
    )
    assert response.status_code == 400


def test_work_missing_404(client_logged_in):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:work", args=["book", 999999])
    )
    assert response.status_code == 404


def test_work_get_not_owned(client_logged_in, book):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:work", args=["book", book.pk])
    )
    assert response.status_code == 200
    assert response.context["owned"] is False
    assert response.context["user_work"] is None


def test_work_get_owned(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:work", args=["book", book.pk])
    )
    assert response.status_code == 200
    assert response.context["owned"] is True
    assert response.context["user_work"] == uw


# ─── artwork_delete ─────────────────────────────────────────────────────────


def test_delete_requires_login(client):
    response = client.post(reverse("vor_archives:artworks:delete"), {"ids": "1"})
    assert response.status_code == 302


def test_delete_get_405(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:delete"))
    assert response.status_code == 405


def test_delete_removes_userwork(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:delete"), {"ids": [str(uw.pk)]}
    )
    assert response.status_code == 200
    assert not UserWork.objects.filter(pk=uw.pk).exists()
    trigger = json.loads(response["HX-Trigger"])
    assert trigger.get("vor:reload-list") is True
    assert trigger.get("vor:close-overlay") is True


def test_delete_empty_ids_noop(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(reverse("vor_archives:artworks:delete"), {})
    assert response.status_code == 200
    assert UserWork.objects.filter(pk=uw.pk).exists()
