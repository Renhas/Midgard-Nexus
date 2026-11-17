"""Tests for apps.vor_archives.artworks.services.works - crud.

Covers _attach_work (creating UserWork, position handling, owned_platforms
m2m) and attach_work_from_form (form-driven attach with clamping and
AlreadyAttached), plus reorder_user_works (normalizing positions).
"""

from decimal import Decimal

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.forms import AttachWorkForm
from apps.vor_archives.artworks.services import (
    AlreadyAttached,
    attach_work_from_form,
    reorder_user_works,
)
from apps.vor_archives.artworks.services.works import _attach_work
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    GameFactory,
    PlatformFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

# ─── _attach_work ───────────────────────────────────────────────────────────


def test_attach_work_first_uw_gets_position_zero(user, book):
    uw, created = _attach_work(user, book)

    assert created is True
    assert uw.user == user
    assert uw.work_object_id == book.pk
    assert uw.order_position == 0


def test_attach_work_increments_position(user, movie, book):
    UserWorkFactory(user=user, work=movie)

    uw, _ = _attach_work(user, book)

    assert uw.order_position == 1


def test_attach_work_respects_explicit_order_position(user, book):
    uw, _ = _attach_work(user, book, {"order_position": 42})

    assert uw.order_position == 42


def test_attach_work_applies_owned_platforms(user, game):
    platform = PlatformFactory()

    uw, created = _attach_work(
        user,
        game,
        {
            "status": UserWorkStatusChoices.COMPLETED,
            "rating": 9,
            "owned_platforms": [platform],
        },
    )

    assert created is True
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.rating == 9
    assert list(uw.owned_platforms.all()) == [platform]


def test_attach_work_existing_does_not_touch_platforms(user, book):
    UserWorkFactory(user=user, work=book)
    platform = PlatformFactory()

    uw, created = _attach_work(user, book, {"owned_platforms": [platform]})

    assert created is False
    assert list(uw.owned_platforms.all()) == []


# ─── attach_work_from_form ──────────────────────────────────────────────────


def test_attach_work_from_form_creates(user, book):
    form = AttachWorkForm(data={"work_type": "book", "work_id": str(book.pk)})
    assert form.is_valid()

    uw, created = attach_work_from_form(user, form)

    assert created is True
    assert uw.user == user
    assert uw.work_object_id == book.pk
    assert uw.status == UserWorkStatusChoices.PLANNING


def test_attach_work_from_form_raises_already_attached(user, book):
    UserWorkFactory(user=user, work=book)
    form = AttachWorkForm(data={"work_type": "book", "work_id": str(book.pk)})
    assert form.is_valid()

    with pytest.raises(AlreadyAttached) as exc_info:
        attach_work_from_form(user, form)
    assert exc_info.value.work == book


def test_attach_work_from_form_clamps_progress(user):
    book = BookFactory(pages=100)
    form = AttachWorkForm(
        data={"work_type": "book", "work_id": str(book.pk), "progress": "999"}
    )
    assert form.is_valid()

    uw, _ = attach_work_from_form(user, form)

    assert uw.progress == Decimal("100")


def test_attach_work_from_form_keeps_progress_below_max(user):
    book = BookFactory(pages=100)
    form = AttachWorkForm(
        data={"work_type": "book", "work_id": str(book.pk), "progress": "50"}
    )
    assert form.is_valid()

    uw, _ = attach_work_from_form(user, form)

    assert uw.progress == Decimal("50")


def test_attach_work_from_form_does_not_clamp_game(user):
    game = GameFactory()
    form = AttachWorkForm(
        data={"work_type": "game", "work_id": str(game.pk), "progress": "9999"}
    )
    assert form.is_valid()

    uw, _ = attach_work_from_form(user, form)

    assert uw.progress == Decimal("9999")


# ─── reorder_user_works ─────────────────────────────────────────────────────


def test_reorder_normalizes_non_unique_positions(user, book, movie):
    uw1 = UserWork.objects.create(user=user, work=book)
    uw2 = UserWork.objects.create(user=user, work=movie)
    UserWork.objects.filter(pk__in=[uw1.pk, uw2.pk]).update(order_position=0)

    reorder_user_works(user, [uw1.pk, uw2.pk])

    uw1.refresh_from_db()
    uw2.refresh_from_db()
    assert uw1.order_position == 0
    assert uw2.order_position == 1


def test_reorder_normalizes_gaps_in_positions(user, book, movie, game):
    uw1 = UserWork.objects.create(user=user, work=book, order_position=5)
    uw2 = UserWork.objects.create(user=user, work=movie, order_position=10)
    uw3 = UserWork.objects.create(user=user, work=game, order_position=15)

    reorder_user_works(user, [uw1.pk, uw2.pk, uw3.pk])

    uw1.refresh_from_db()
    uw2.refresh_from_db()
    uw3.refresh_from_db()
    assert (uw1.order_position, uw2.order_position, uw3.order_position) == (0, 1, 2)


def test_reorder_ignores_foreign_ids(user, book):
    other_user = UserFactory()
    uw = UserWork.objects.create(user=user, work=book)
    foreign = UserWork.objects.create(user=other_user, work=BookFactory())

    result = reorder_user_works(user, [uw.pk, foreign.pk])

    assert result == 1
    foreign.refresh_from_db()
    assert foreign.order_position == 0


def test_reorder_empty_list_returns_zero(user):
    assert reorder_user_works(user, []) == 0
