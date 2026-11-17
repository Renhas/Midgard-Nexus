"""Tests for apps.vor_archives.artworks.services.works - deletion.

Covers orphan_works detection and delete_user_works cascade, including
shared works, foreign ids, empty input and feed item cleanup.
"""

import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    delete_user_works,
    orphan_works,
)
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.models import (
    Book,
    CompletionRecord,
    FeedItem,
    UserWork,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    UserWorkFactory,
)

pytestmark = pytest.mark.django_db

# ─── orphan_works ────────────────────────────────────────────────────────────


def test_orphan_works_single_owner(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert orphan_works([uw]) == [book]


def test_orphan_works_shared_is_not_orphan(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=other, work=book)

    assert orphan_works([uw]) == []


def test_orphan_works_empty_input():
    assert orphan_works([]) == []


def test_orphan_works_deduplicates(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert orphan_works([uw, uw]) == [book]


def test_orphan_works_multiple(user, book, movie):
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)

    assert set(orphan_works([uw_book, uw_movie])) == {book, movie}


# ─── delete_user_works ───────────────────────────────────────────────────────


def test_delete_user_works_removes_userwork(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert delete_user_works(user, [uw.pk]) == 1
    assert not UserWork.objects.filter(pk=uw.pk).exists()


def test_delete_user_works_deletes_orphan_work(user, book):
    uw = UserWorkFactory(user=user, work=book)

    delete_user_works(user, [uw.pk])

    assert not Book.objects.filter(pk=book.pk).exists()


def test_delete_user_works_keeps_shared_work(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=other, work=book)

    delete_user_works(user, [uw.pk])

    assert Book.objects.filter(pk=book.pk).exists()


def test_delete_user_works_ignores_foreign_ids(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    foreign = UserWorkFactory(user=other, work=BookFactory())

    assert delete_user_works(user, [uw.pk, foreign.pk]) == 1
    assert UserWork.objects.filter(pk=foreign.pk).exists()


def test_delete_user_works_empty_list(user):
    assert delete_user_works(user, []) == 0


def test_delete_user_works_removes_feed_items_and_completion_records(user, book):
    uw = UserWorkFactory(user=user, work=book)
    uw.status = UserWorkStatusChoices.COMPLETED
    uw.save()

    assert FeedItem.objects.filter(user_work_id=uw.pk).exists()
    assert CompletionRecord.objects.filter(user_work_id=uw.pk).exists()

    delete_user_works(user, [uw.pk])

    assert not FeedItem.objects.filter(user_work_id=uw.pk).exists()
    # CompletionRecord cascades via FK CASCADE
    assert not CompletionRecord.objects.filter(user_work_id=uw.pk).exists()
