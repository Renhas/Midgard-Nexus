"""Tests for apps.vor_archives signals."""

import pytest
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

from apps.vor_archives.constants import (
    FeedItemActionTypeChoices,
    UserWorkStatusChoices,
)
from apps.vor_archives.models import (
    CompletionRecord,
    FeedItem,
    UserWork,
)
from apps.vor_archives.tests.factories import UserWorkFactory

pytestmark = pytest.mark.django_db


def test_userwork_create_default_status_creates_added_and_planning_feed_items(
    user, book
):
    uw = UserWorkFactory(user=user, work=book)

    actions = list(
        FeedItem.objects.filter(user=user, user_work=uw)
        .order_by("pk")
        .values_list("action_type", flat=True)
    )
    assert actions == [
        FeedItemActionTypeChoices.ADDED,
        FeedItemActionTypeChoices.PLANNING,
    ]
    assert not CompletionRecord.objects.filter(user_work=uw).exists()
    assert uw.times_completed == 0
    assert uw.last_completed_date is None


@pytest.mark.parametrize(
    "status",
    [
        UserWorkStatusChoices.PLANNING,
        UserWorkStatusChoices.IN_PROGRESS,
        UserWorkStatusChoices.DROPPED,
    ],
)
def test_userwork_create_with_non_completed_status_creates_feed_items(
    user, book, status
):
    uw = UserWorkFactory(user=user, work=book, status=status)

    actions = list(
        FeedItem.objects.filter(user=user, user_work=uw)
        .order_by("pk")
        .values_list("action_type", flat=True)
    )
    assert actions == [FeedItemActionTypeChoices.ADDED, status]
    assert not CompletionRecord.objects.filter(user_work=uw).exists()


def test_userwork_create_with_completed_status_creates_completion_and_feed_items(
    user, book
):
    uw = UserWorkFactory(
        user=user,
        work=book,
        status=UserWorkStatusChoices.COMPLETED,
    )

    actions = list(
        FeedItem.objects.filter(user=user, user_work=uw)
        .order_by("pk")
        .values_list("action_type", flat=True)
    )
    assert actions == [
        FeedItemActionTypeChoices.ADDED,
        FeedItemActionTypeChoices.COMPLETED,
    ]
    assert uw.times_completed == 1
    assert uw.last_completed_date == timezone.now().date()
    assert CompletionRecord.objects.filter(user_work=uw).count() == 1


def test_userwork_create_with_rating_creates_rated_feed_item(user, book):
    uw = UserWorkFactory(
        user=user,
        work=book,
        status=UserWorkStatusChoices.IN_PROGRESS,
        rating=8,
    )

    actions = list(
        FeedItem.objects.filter(user=user, user_work=uw)
        .order_by("pk")
        .values_list("action_type", flat=True)
    )
    assert actions == [
        FeedItemActionTypeChoices.ADDED,
        FeedItemActionTypeChoices.IN_PROGRESS,
        FeedItemActionTypeChoices.RATED,
    ]


def test_userwork_update_without_changes_does_not_duplicate_feed_items(user, book):
    uw = UserWorkFactory(user=user, work=book, rating=7)
    initial_count = FeedItem.objects.filter(user=user, user_work=uw).count()

    uw.is_hidden = True
    uw.save()

    assert FeedItem.objects.filter(user=user, user_work=uw).count() == initial_count


def test_userwork_update_status_creates_status_feed_item(user, book):
    uw = UserWorkFactory(
        user=user,
        work=book,
        status=UserWorkStatusChoices.PLANNING,
    )

    uw.status = UserWorkStatusChoices.IN_PROGRESS
    uw.save()

    actions = list(
        FeedItem.objects.filter(user=user, user_work=uw)
        .order_by("pk")
        .values_list("action_type", flat=True)
    )
    assert actions == [
        FeedItemActionTypeChoices.ADDED,
        FeedItemActionTypeChoices.PLANNING,
        FeedItemActionTypeChoices.IN_PROGRESS,
    ]


def test_userwork_update_to_completed_increments_completions_and_creates_record(
    user, book
):
    uw = UserWorkFactory(
        user=user,
        work=book,
        status=UserWorkStatusChoices.IN_PROGRESS,
    )

    uw.status = UserWorkStatusChoices.COMPLETED
    uw.save()

    uw.refresh_from_db()
    assert uw.times_completed == 1
    assert uw.last_completed_date == timezone.now().date()
    assert CompletionRecord.objects.filter(user_work=uw).count() == 1
    assert FeedItem.objects.filter(
        user=user,
        user_work=uw,
        action_type=FeedItemActionTypeChoices.COMPLETED,
    ).exists()


def test_userwork_update_rating_creates_rated_feed_item(user, book):
    uw = UserWorkFactory(user=user, work=book, rating=None)

    uw.rating = 9
    uw.save()

    assert (
        FeedItem.objects.filter(
            user=user,
            user_work=uw,
            action_type=FeedItemActionTypeChoices.RATED,
        ).count()
        == 1
    )

    uw.rating = 10
    uw.save()

    assert (
        FeedItem.objects.filter(
            user=user,
            user_work=uw,
            action_type=FeedItemActionTypeChoices.RATED,
        ).count()
        == 2
    )


def test_userwork_raw_save_skips_signals(user, book):
    uw = UserWorkFactory.build(
        user=user,
        work=book,
        status=UserWorkStatusChoices.COMPLETED,
        rating=10,
        date_added=timezone.now(),
    )
    pre_save.send(sender=UserWork, instance=uw, raw=True)
    uw.save_base(raw=True)
    post_save.send(sender=UserWork, instance=uw, created=True, raw=True)

    assert not FeedItem.objects.filter(user=user, user_work=uw).exists()
    assert not CompletionRecord.objects.filter(user_work=uw).exists()
    assert uw.times_completed == 0
