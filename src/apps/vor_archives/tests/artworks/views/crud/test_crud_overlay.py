"""Tests for artwork_detail, artwork_work and artwork_delete views."""

import json
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    GameFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
    WorkRelationFactory,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


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


# ─── artwork_detail: type-specific context ──────────────────────────────────


def test_detail_film_movie_units(client_logged_in, user, movie):
    uw = UserWorkFactory(user=user, work=movie)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    assert response.context["progress_unit"] == "мин."


def test_detail_tv_show_units(client_logged_in, user, tv_show):
    uw = UserWorkFactory(user=user, work=tv_show)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    assert response.context["progress_unit"] == "эп."


def test_detail_game_units_and_platforms_visible(client_logged_in, user, game):
    uw = UserWorkFactory(user=user, work=game)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    assert response.context["progress_unit"] == "ч."
    assert response.context["hide_platforms"] is False


def test_detail_book_hides_platforms(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.context["hide_platforms"] is True


def test_detail_with_m2m(client_logged_in, user, book):
    person = PersonFactory(name="Tolkien", bio="Author")
    tag = TagFactory()
    genre = BookGenreFactory()
    book.authors.add(person)
    book.tags.add(tag)
    book.genres.add(genre)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    opts = response.context["overlay_opts"]
    assert opts["authors"] == [{"id": person.pk, "name": "Tolkien", "tip": "Author"}]
    assert len(opts["tags"]) == 1
    assert opts["tags"][0]["id"] == tag.pk
    assert len(opts["genres"]) == 1
    assert opts["genres"][0]["id"] == genre.pk


def test_detail_with_relations(client_logged_in, user, book):
    other = BookFactory()
    WorkRelationFactory(source=book, target=other)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:detail", args=[uw.pk])
    )
    assert response.status_code == 200
    relations = response.context["work_relations"]
    assert len(relations) == 1
    assert relations[0]["direction"] == "out"
    assert relations[0]["work_id"] == other.pk


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


# ─── artwork_overlay_response: staff-only paths ─────────────────────────────


def test_staff_post_clears_cover(staff_client, staff_user):
    book = BookFactory(cover="covers/test.jpg")
    uw = UserWorkFactory(user=staff_user, work=book)
    response = staff_client.post(
        reverse("vor_archives:artworks:detail", args=[uw.pk]),
        {
            "title": book.title,
            "pages": book.pages,
            "cover_clear": "1",
        },
    )
    assert response.status_code == 200
    book.refresh_from_db()
    assert not book.cover


def test_staff_post_game_prunes_stale_platforms(staff_client, staff_user):
    p1 = PlatformFactory()
    p2 = PlatformFactory()
    game = GameFactory()
    game.platforms.set([p1, p2])
    uw = UserWorkFactory(user=staff_user, work=game)
    uw.owned_platforms.set([p1, p2])
    response = staff_client.post(
        reverse("vor_archives:artworks:detail", args=[uw.pk]),
        {"title": game.title, "platforms": [str(p1.pk)]},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert set(uw.owned_platforms.values_list("pk", flat=True)) == {p1.pk}


def test_staff_post_relation_validation_error(staff_client, staff_user, book):
    uw = UserWorkFactory(user=staff_user, work=book)
    with mock.patch(
        "apps.vor_archives.artworks.views.utils.artworks.sync_work_relations",
        side_effect=ValidationError("conflict"),
    ):
        response = staff_client.post(
            reverse("vor_archives:artworks:detail", args=[uw.pk]),
            {"title": "Updated", "pages": "100"},
        )
    assert response.status_code == 200
    assert response.context["editing"] is True
    work_form = response.context["work_form"]
    assert not work_form.is_valid()
    assert work_form.non_field_errors()
    # Documents current behavior: form save is not inside an atomic block,
    # so the updated title persists even though relation sync failed.
    book.refresh_from_db()
    assert book.title == "Updated"
