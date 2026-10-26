"""Tests for artwork_quick view: inline field updates from the list."""

import json
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.tests.factories import (
    BookFactory,
    GameFactory,
    PlatformFactory,
    UserWorkFactory,
    UserFactory,
)


pytestmark = pytest.mark.django_db


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


def test_quick_status_in_progress_from_planning_keeps_progress(
    client_logged_in, user, book
):
    uw = UserWorkFactory(
        user=user,
        work=book,
        progress=Decimal("50"),
        status=UserWorkStatusChoices.PLANNING,
    )
    response = client_logged_in.post(
        reverse("vor_archives:artworks:quick", args=[uw.pk]),
        {"field": "status", "value": UserWorkStatusChoices.IN_PROGRESS},
    )
    assert response.status_code == 200
    uw.refresh_from_db()
    assert uw.progress == Decimal("50")


@pytest.mark.parametrize(
    "old_status",
    [UserWorkStatusChoices.COMPLETED, UserWorkStatusChoices.DROPPED],
)
def test_quick_status_in_progress_from_terminal_resets_progress(
    client_logged_in, user, book, old_status
):
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))
    UserWork = type(uw)
    UserWork.objects.filter(pk=uw.pk).update(status=old_status)
    uw.refresh_from_db()
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
