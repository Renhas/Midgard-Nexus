"""Tests for apps.vor_archives.artworks.services.works - crud.

Covers attach_work (creating UserWork, position handling, cleaned data
application) and reorder_user_works (normalizing positions).
"""

import pytest
from django.http import Http404

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    attach_work,
    reorder_user_works,
)
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    PlatformFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

# ─── attach_work ─────────────────────────────────────────────────────────────


def test_attach_work_creates_new(user, book):
    uw, created = attach_work(user, "book", book.pk)

    assert created is True
    assert uw.user == user
    assert uw.work_object_id == book.pk


def test_attach_work_returns_existing(user, book):
    existing = UserWorkFactory(user=user, work=book)

    uw, created = attach_work(user, "book", book.pk)

    assert created is False
    assert uw.pk == existing.pk


def test_attach_work_first_uw_gets_position_zero(user, book):
    uw, _ = attach_work(user, "book", book.pk)

    assert uw.order_position == 0


def test_attach_work_increments_position(user, movie, book):
    UserWorkFactory(user=user, work=movie)

    uw, _ = attach_work(user, "book", book.pk)

    assert uw.order_position == 1


def test_attach_work_respects_explicit_order_position(user, book):
    uw, _ = attach_work(user, "book", book.pk, cleaned_user_data={"order_position": 42})

    assert uw.order_position == 42


def test_attach_work_applies_cleaned_user_data(user, book):
    platform = PlatformFactory()

    uw, created = attach_work(
        user,
        "book",
        book.pk,
        cleaned_user_data={
            "status": UserWorkStatusChoices.COMPLETED,
            "rating": 9,
            "owned_platforms": [platform],
        },
    )

    assert created is True
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.rating == 9
    assert list(uw.owned_platforms.all()) == [platform]


def test_attach_work_does_not_touch_platforms_on_existing(user, book):
    UserWorkFactory(user=user, work=book)
    platform = PlatformFactory()

    uw, created = attach_work(
        user, "book", book.pk, cleaned_user_data={"owned_platforms": [platform]}
    )

    assert created is False
    assert list(uw.owned_platforms.all()) == []


def test_attach_work_unknown_type_raises(user):
    with pytest.raises(ValueError):
        attach_work(user, "nope", 1)


def test_attach_work_missing_work_raises_404(user):
    with pytest.raises(Http404):
        attach_work(user, "book", 999999)


# ─── reorder_user_works ─────────────────


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
