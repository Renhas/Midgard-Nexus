"""Tests for apps.vor_archives.artworks.views.actions."""

import json
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    GameFactory,
    PlatformFactory,
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


# ─── artwork_reorder ────────────────────────────────────────────────────────


def test_reorder_requires_login(client):
    response = client.post(reverse("vor_archives:artworks:reorder"))
    assert response.status_code == 302


def test_reorder_get_405(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:reorder"))
    assert response.status_code == 405


def test_reorder_ok(client_logged_in, user, book, movie):
    uw1 = UserWorkFactory(user=user, work=book)
    uw2 = UserWorkFactory(user=user, work=movie)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:reorder"),
        {"ids": [str(uw2.pk), str(uw1.pk)]},
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}
    uw1.refresh_from_db()
    uw2.refresh_from_db()
    assert uw2.order_position == 0
    assert uw1.order_position == 1


# ─── artwork_attach ─────────────────────────────────────────────────────────


def test_attach_missing_fields_400(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:attach"), {})
    assert response.status_code == 400


def test_attach_missing_work_id_400(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"), {"work_type": "book"}
    )
    assert response.status_code == 400


def test_attach_already_owned_json_400(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["ok"] is False
    assert payload["error"] == "already"


def test_attach_already_owned_html_renders_preview(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
    )
    assert response.status_code == 200
    assert response.context["already"] is True
    assert response.context["work"] == book


def test_attach_invalid_status_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "status": "bogus"},
    )
    assert response.status_code == 400


def test_attach_invalid_rating_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "rating": "11"},
    )
    assert response.status_code == 400


def test_attach_rating_zero_treated_as_none(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "rating": "0",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    uw = UserWork.objects.get(user=user)
    assert uw.rating is None


def test_attach_invalid_progress_400(client_logged_in, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk), "progress": "abc"},
    )
    assert response.status_code == 400


def test_attach_negative_progress_clamped(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "progress": "-5",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    uw = UserWork.objects.get(user=user)
    assert uw.progress == Decimal("0")


def test_attach_valid_json_creates_userwork(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {
            "work_type": "book",
            "work_id": str(book.pk),
            "status": UserWorkStatusChoices.IN_PROGRESS,
            "rating": "8",
            "progress": "42.5",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"ok": True}
    uw = UserWork.objects.get(user=user, work_object_id=book.pk)
    assert uw.status == UserWorkStatusChoices.IN_PROGRESS
    assert uw.rating == 8
    assert uw.progress == Decimal("42.5")


def test_attach_valid_html_returns_trigger(client_logged_in, user, book):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:attach"),
        {"work_type": "book", "work_id": str(book.pk)},
    )
    assert response.status_code == 200
    trigger = json.loads(response["HX-Trigger"])
    assert trigger.get("vor:reload-list") is True
    assert trigger.get("vor:close-overlay") is True


# ─── artwork_delete_preview ─────────────────────────────────────────────────


def test_delete_preview_requires_login(client):
    response = client.get(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 302


def test_delete_preview_get_only(client_logged_in):
    response = client_logged_in.post(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 405


def test_delete_preview_empty(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:delete_preview"))
    assert response.status_code == 200
    assert response.context["count"] == 0
    assert response.context["ids"] == []
    assert response.context["orphan_titles"] == []


def test_delete_preview_own_uw(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(uw.pk)]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 1
    assert response.context["orphan_titles"] == [book.title]


def test_delete_preview_foreign_uw_ignored(client_logged_in, book):
    other = UserFactory()
    foreign = UserWorkFactory(user=other, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(foreign.pk)]},
    )
    assert response.status_code == 200
    assert response.context["count"] == 0


def test_delete_preview_shared_work_not_orphan(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    other = UserFactory()
    UserWorkFactory(user=other, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:delete_preview"),
        {"ids": [str(uw.pk)]},
    )
    assert response.status_code == 200
    assert response.context["orphan_titles"] == []


# ─── artwork_preview ────────────────────────────────────────────────────────


def test_preview_requires_login(client, book):
    response = client.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 302


def test_preview_missing_work_id_400(client_logged_in):
    response = client_logged_in.get(reverse("vor_archives:artworks:preview"))
    assert response.status_code == 400


def test_preview_default_type_book(client_logged_in, book):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 200
    assert response.context["work_type"] == "book"
    assert response.context["work"] == book


def test_preview_explicit_type(client_logged_in, movie):
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"),
        {"type": "film", "work_id": movie.pk},
    )
    assert response.status_code == 200
    assert response.context["work_type"] == "film"


def test_preview_already_owned(client_logged_in, user, book):
    UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:preview"), {"work_id": book.pk}
    )
    assert response.status_code == 200
    assert response.context["already"] is True


# ─── artwork_quick ──────────────────────────────────────────────────────────


def test_quick_requires_login(client, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": "completed"},
    )
    assert response.status_code == 302


def test_quick_get_405(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.get(
        reverse("vor_archives:artworks:quick", args=[uw.pk])
    )
    assert response.status_code == 405


def test_quick_missing_uw_404(client_logged_in):
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[999999]),
        {"field": "status", "value": "completed"},
    )
    assert response.status_code == 404


def test_quick_foreign_uw_404(client_logged_in):
    other = UserFactory()
    uw = UserWorkFactory(user=other, work=BookFactory())
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": "completed"},
    )
    assert response.status_code == 404


def test_quick_unknown_field_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "bogus", "value": "x"},
    )
    assert response.status_code == 400


def test_quick_invalid_status_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": "bogus"},
    )
    assert response.status_code == 400


def test_quick_status_completed_sets_progress_to_max(client_logged_in, user):
    book = BookFactory(pages=100)
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": UserWorkStatusChoices.COMPLETED},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("100")
    assert uw.status == UserWorkStatusChoices.COMPLETED


def test_quick_status_in_progress_resets_progress(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": UserWorkStatusChoices.IN_PROGRESS},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("0")


def test_quick_progress_invalid_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "progress", "value": "abc"},
    )
    assert response.status_code == 400


def test_quick_progress_at_max_marks_completed(client_logged_in, user):
    book = BookFactory(pages=100)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "progress", "value": "100"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("100")
    assert uw.status == UserWorkStatusChoices.COMPLETED


def test_quick_progress_above_max_clamped(client_logged_in, user):
    book = BookFactory(pages=100)
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "progress", "value": "999"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("100")


def test_quick_progress_negative_clamped_to_zero(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "progress", "value": "-5"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("0")


def test_quick_rating_valid(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "rating", "value": "7"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.rating == 7


def test_quick_rating_empty_clears(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book, rating=5)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "rating", "value": ""},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.rating is None


def test_quick_rating_out_of_range_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "rating", "value": "11"},
    )
    assert response.status_code == 400


def test_quick_is_hidden(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "is_hidden", "value": "1"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.is_hidden is True


def test_quick_times_completed_negative_clamped(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "times_completed", "value": "-3"},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.times_completed == 0


def test_quick_times_completed_invalid_400(client_logged_in, user, book):
    uw = UserWorkFactory(user=user, work=book)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "times_completed", "value": "abc"},
    )
    assert response.status_code == 400


def test_quick_owned_platform_unknown_400(client_logged_in, user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "owned_platform", "value": "999999"},
    )
    assert response.status_code == 400


def test_quick_owned_platform_not_related_to_work_400(client_logged_in, user):
    game = GameFactory()
    unrelated = PlatformFactory()
    uw = UserWorkFactory(user=user, work=game)
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "owned_platform", "value": str(unrelated.pk)},
    )
    assert response.status_code == 400


def test_quick_owned_platform_toggles(client_logged_in, user):
    game = GameFactory()
    platform = PlatformFactory()
    game.platforms.add(platform)
    uw = UserWorkFactory(user=user, work=game)
    url = reverse("vor_archives:artworks:quick", args=[uw.pk])

    response = client_logged_in.post(
        url, {"field": "owned_platform", "value": str(platform.pk)}
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["owned_platform_ids"] == [platform.pk]

    response = client_logged_in.post(
        url, {"field": "owned_platform", "value": str(platform.pk)}
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["owned_platform_ids"] == []


def test_quick_progress_game_no_maximum_not_clamped(client_logged_in, user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game, progress=Decimal("100"))
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "progress", "value": "999"},
    )
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["progress"] == 999.0
    uw.refresh_from_db()
    assert uw.progress == Decimal("999")
    assert uw.status == UserWorkStatusChoices.PLANNING


def test_quick_status_completed_game_keeps_progress(client_logged_in, user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game, progress=Decimal("42"))
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": UserWorkStatusChoices.COMPLETED},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.progress == Decimal("42")
