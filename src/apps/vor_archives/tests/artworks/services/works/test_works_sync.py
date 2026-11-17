"""Tests for apps.vor_archives.artworks.services.works - sync_work_relations.

Covers creation, type updates, deletion of unlisted outgoing and incoming
relations, self-relation skip and 404 for missing targets.
"""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from apps.vor_archives.artworks.services import sync_work_relations
from apps.vor_archives.constants import WorkRelationTypeChoices
from apps.vor_archives.models import (
    Book,
    WorkRelation,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    WorkRelationFactory,
)

pytestmark = pytest.mark.django_db

# ─── sync_work_relations ────────────────────────────────────────────────────


def test_sync_work_relations_creates_new_outgoing(book):
    target = BookFactory()

    sync_work_relations(
        book,
        [
            {
                "type_key": "book",
                "work_id": target.pk,
                "relation_type": WorkRelationTypeChoices.SEQUEL,
            }
        ],
    )

    book_ct = ContentType.objects.get_for_model(Book)
    assert WorkRelation.objects.filter(
        source_content_type=book_ct,
        source_object_id=book.pk,
        target_content_type=book_ct,
        target_object_id=target.pk,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    ).exists()


def test_sync_work_relations_updates_existing_type(book):
    other = BookFactory()
    rel = WorkRelationFactory(
        source=book,
        target=other,
        relation_type=WorkRelationTypeChoices.OTHER,
    )

    sync_work_relations(
        book,
        [{"id": rel.pk, "relation_type": WorkRelationTypeChoices.SEQUEL}],
    )

    rel.refresh_from_db()
    assert rel.relation_type == WorkRelationTypeChoices.SEQUEL


def test_sync_work_relations_preserves_listed_relation(book):
    other = BookFactory()
    rel = WorkRelationFactory(
        source=book,
        target=other,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )

    sync_work_relations(
        book,
        [{"id": rel.pk, "relation_type": WorkRelationTypeChoices.SEQUEL}],
    )

    assert WorkRelation.objects.filter(pk=rel.pk).exists()


def test_sync_work_relations_deletes_unlisted_outgoing(book):
    other = BookFactory()
    rel = WorkRelationFactory(source=book, target=other)

    sync_work_relations(book, [])

    assert not WorkRelation.objects.filter(pk=rel.pk).exists()


def test_sync_work_relations_deletes_unlisted_incoming(book):
    """Documents current behavior: incoming relations are also removed."""
    other = BookFactory()
    rel = WorkRelationFactory(source=other, target=book)

    sync_work_relations(book, [])

    assert not WorkRelation.objects.filter(pk=rel.pk).exists()


def test_sync_work_relations_skips_self_relation(book):
    sync_work_relations(
        book,
        [
            {
                "type_key": "book",
                "work_id": book.pk,
                "relation_type": WorkRelationTypeChoices.SEQUEL,
            }
        ],
    )

    book_ct = ContentType.objects.get_for_model(Book)
    assert not WorkRelation.objects.filter(
        source_content_type=book_ct,
        source_object_id=book.pk,
        target_content_type=book_ct,
        target_object_id=book.pk,
    ).exists()


def test_sync_work_relations_skips_items_without_payload(book):
    sync_work_relations(book, [{}])

    assert not WorkRelation.objects.exists()


def test_sync_work_relations_ignores_unknown_relation_id(book):
    sync_work_relations(book, [{"id": 999999}])

    # Only risk is that no relations were deleted erroneously; nothing to assert about existence.
    assert not WorkRelation.objects.exists()


def test_sync_work_relations_invalid_target_raises_404(book):
    with pytest.raises(Http404):
        sync_work_relations(book, [{"type_key": "book", "work_id": 999999}])


def test_sync_work_relations_ignores_relation_of_other_work(book):
    other_a = BookFactory()
    other_b = BookFactory()
    foreign_rel = WorkRelationFactory(
        source=other_a,
        target=other_b,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )

    sync_work_relations(
        book,
        [{"id": foreign_rel.pk, "relation_type": WorkRelationTypeChoices.OTHER}],
    )

    foreign_rel.refresh_from_db()
    assert foreign_rel.relation_type == WorkRelationTypeChoices.SEQUEL
