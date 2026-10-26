"""Tests for apps.vor_archives.artworks.services.quick."""

from decimal import Decimal

import pytest

from apps.vor_archives.artworks.services import (
    PlatformNotRelated,
    quick_update,
)
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    GameFactory,
    PlatformFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

# ─── status ─────────────────────────────────────────────────────────────────


def test_status_completed_book_sets_progress_to_max(user):
    book = BookFactory(pages=100)
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))

    quick_update(uw, "status", UserWorkStatusChoices.COMPLETED)

    uw.refresh_from_db()
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.progress == Decimal("100")


def test_status_completed_game_keeps_progress(user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game, progress=Decimal("42"))

    quick_update(uw, "status", UserWorkStatusChoices.COMPLETED)

    uw.refresh_from_db()
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.progress == Decimal("42")


def test_status_in_progress_from_planning_keeps_progress(user, book):
    uw = UserWorkFactory(
        user=user,
        work=book,
        progress=Decimal("50"),
        status=UserWorkStatusChoices.PLANNING,
    )

    quick_update(uw, "status", UserWorkStatusChoices.IN_PROGRESS)

    uw.refresh_from_db()
    assert uw.status == UserWorkStatusChoices.IN_PROGRESS
    assert uw.progress == Decimal("50")


@pytest.mark.parametrize(
    "old_status",
    [UserWorkStatusChoices.COMPLETED, UserWorkStatusChoices.DROPPED],
)
def test_status_in_progress_from_terminal_resets_progress(user, book, old_status):
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))
    UserWork.objects.filter(pk=uw.pk).update(status=old_status)
    uw.refresh_from_db()

    quick_update(uw, "status", UserWorkStatusChoices.IN_PROGRESS)

    uw.refresh_from_db()
    assert uw.progress == Decimal("0")


# ─── progress ───────────────────────────────────────────────────────────────


def test_progress_above_max_clamped_and_completes(user):
    book = BookFactory(pages=100)
    uw = UserWorkFactory(user=user, work=book)

    quick_update(uw, "progress", Decimal("999"))

    uw.refresh_from_db()
    assert uw.progress == Decimal("100")
    assert uw.status == UserWorkStatusChoices.COMPLETED


def test_progress_below_max_keeps_status(user, book):
    uw = UserWorkFactory(
        user=user,
        work=book,
        progress=Decimal("50"),
        status=UserWorkStatusChoices.PLANNING,
    )

    quick_update(uw, "progress", Decimal("60"))

    uw.refresh_from_db()
    assert uw.progress == Decimal("60")
    assert uw.status == UserWorkStatusChoices.PLANNING


def test_progress_game_not_clamped(user):
    game = GameFactory()
    uw = UserWorkFactory(user=user, work=game)

    quick_update(uw, "progress", Decimal("999"))

    uw.refresh_from_db()
    assert uw.progress == Decimal("999")
    assert uw.status == UserWorkStatusChoices.PLANNING


# ─── rating ─────────────────────────────────────────────────────────────────


def test_rating_set(user, book):
    uw = UserWorkFactory(user=user, work=book)

    quick_update(uw, "rating", 7)

    uw.refresh_from_db()
    assert uw.rating == 7


def test_rating_none_clears(user, book):
    uw = UserWorkFactory(user=user, work=book, rating=5)

    quick_update(uw, "rating", None)

    uw.refresh_from_db()
    assert uw.rating is None


# ─── is_hidden ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", [True, False])
def test_is_hidden(user, book, value):
    uw = UserWorkFactory(user=user, work=book, is_hidden=not value)

    quick_update(uw, "is_hidden", value)

    uw.refresh_from_db()
    assert uw.is_hidden is value


# ─── times_completed ────────────────────────────────────────────────────────


def test_times_completed_set(user, book):
    uw = UserWorkFactory(user=user, work=book)

    quick_update(uw, "times_completed", 3)

    uw.refresh_from_db()
    assert uw.times_completed == 3


# ─── owned_platform ─────────────────────────────────────────────────────────


def test_owned_platform_toggles_on(user):
    game = GameFactory()
    platform = PlatformFactory()
    game.platforms.add(platform)
    uw = UserWorkFactory(user=user, work=game)

    payload = quick_update(uw, "owned_platform", platform.pk)

    assert payload["owned_platform_ids"] == [platform.pk]


def test_owned_platform_toggles_off(user):
    game = GameFactory()
    platform = PlatformFactory()
    game.platforms.add(platform)
    uw = UserWorkFactory(user=user, work=game)
    uw.owned_platforms.add(platform)

    payload = quick_update(uw, "owned_platform", platform.pk)

    assert payload["owned_platform_ids"] == []


def test_owned_platform_not_related_raises(user):
    game = GameFactory()
    unrelated = PlatformFactory()
    uw = UserWorkFactory(user=user, work=game)

    with pytest.raises(PlatformNotRelated):
        quick_update(uw, "owned_platform", unrelated.pk)


def test_owned_platform_work_missing_raises(user, book):
    uw = UserWorkFactory(user=user, work=book)
    UserWork.objects.filter(pk=uw.pk).update(work_object_id=999999)
    uw.refresh_from_db()
    platform = PlatformFactory()

    with pytest.raises(PlatformNotRelated):
        quick_update(uw, "owned_platform", platform.pk)


# ─── unknown field ──────────────────────────────────────────────────────────


def test_unknown_field_raises(user, book):
    uw = UserWorkFactory(user=user, work=book)

    with pytest.raises(ValueError):
        quick_update(uw, "bogus", "x")
