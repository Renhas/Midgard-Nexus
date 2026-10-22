"""Tests for apps.vor_archives.artworks.views.crud."""

import json
from unittest import mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.vor_archives.constants import (
    AgeRatingChoices,
    UserWorkStatusChoices,
)
from apps.vor_archives.models import Book, Film, UserWork, WorkRelation
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    CollectionFactory,
    CollectionItemFactory,
    FilmFactory,
    GameFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
    WorkRelationFactory,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


ALL_STATUSES = list(UserWorkStatusChoices.values)
ALL_AGE_RATINGS = list(AgeRatingChoices.values)


def _filters(**overrides):
    params = {"status": ALL_STATUSES, "age_rating": ALL_AGE_RATINGS}
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


# ─── artwork_add: type-specific ─────────────────────────────────────────────


def test_add_post_tv_show(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "film",
            "title": "New Show",
            "duration_minutes": "60",
            "film_type": "tv_show",
            "episode_count": "10",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["progressMax"] == 10
    assert payload["progressUnit"] == "эп."
    assert payload["progressStep"] == 1


def test_add_post_game(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {"work_type": "game", "title": "New Game"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True
    assert payload["progressMax"] is None
    assert payload["progressUnit"] == "ч."
    assert payload["progressStep"] == 0.5


def test_add_post_with_m2m_and_relations(client_logged_in, book):
    person = PersonFactory()
    tag = TagFactory()
    genre = BookGenreFactory()
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "authors": [str(person.pk)],
            "tags": [str(tag.pk)],
            "genres": [str(genre.pk)],
            "relations_json": json.dumps(
                [
                    {
                        "type_key": "book",
                        "work_id": book.pk,
                        "relation_type": "sequel",
                    }
                ]
            ),
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    new_book = Book.objects.get(pk=payload["work_id"])
    assert list(new_book.authors.all()) == [person]
    assert list(new_book.tags.all()) == [tag]
    assert list(new_book.genres.all()) == [genre]
    ct = ContentType.objects.get_for_model(Book)
    assert WorkRelation.objects.filter(
        source_content_type=ct,
        source_object_id=new_book.pk,
        target_content_type=ct,
        target_object_id=book.pk,
    ).exists()


def test_add_post_malformed_authors_list(client_logged_in):
    person = PersonFactory()
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "authors": f"abc,,{person.pk}",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    new_book = Book.objects.get(pk=payload["work_id"])
    assert list(new_book.authors.all()) == [person]


@pytest.mark.parametrize(
    "relations_json",
    [
        pytest.param("{bad", id="invalid-json"),
        pytest.param('"string"', id="not-a-list"),
        pytest.param("[1, 2]", id="list-of-non-dicts"),
        pytest.param('[{"id": "abc"}]', id="invalid-id-string"),
    ],
)
def test_add_post_malformed_relations_json_ok(client_logged_in, relations_json):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:add"),
        {
            "work_type": "book",
            "title": "New Book",
            "pages": "100",
            "relations_json": relations_json,
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["ok"] is True


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


# ─── artwork_list: filter query params ──────────────────────────────────────


def test_list_filter_by_tags(client_logged_in, user):
    tag1 = TagFactory()
    tag2 = TagFactory()
    book1 = BookFactory()
    book1.tags.add(tag1)
    book2 = BookFactory()
    book2.tags.add(tag2)
    UserWorkFactory(user=user, work=book1)
    UserWorkFactory(user=user, work=book2)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(tags=tag1.pk),
    )
    assert response.status_code == 200
    works = response.context["user_works"]
    assert len(works) == 1
    assert works[0].work_object_id == book1.pk


def test_list_filter_by_platform(client_logged_in, user):
    p1 = PlatformFactory()
    p2 = PlatformFactory()
    game1 = GameFactory()
    game1.platforms.add(p1)
    game2 = GameFactory()
    game2.platforms.add(p2)
    UserWorkFactory(user=user, work=game1)
    UserWorkFactory(user=user, work=game2)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:list"),
        _filters(types="game", platform=p1.pk),
    )
    assert response.status_code == 200
    works = response.context["user_works"]
    assert len(works) == 1
    assert works[0].work_object_id == game1.pk
