"""Tests for apps.vor_archives.artworks.services.works - relations.

Covers relation_label and work_relation_items, including direction labels
and dangling GenericForeignKey targets.
"""

import pytest

from apps.vor_archives.artworks.services import work_relation_items
from apps.vor_archives.artworks.services.works import relation_label
from apps.vor_archives.constants import WorkRelationTypeChoices
from apps.vor_archives.models import WorkRelation
from apps.vor_archives.tests.factories import (
    BookFactory,
    WorkRelationFactory,
)


# ─── relation_label ──────────────────────────────────────────────────────────


def test_relation_label_sequel_both_directions():
    assert relation_label(WorkRelationTypeChoices.SEQUEL, "out") == "Продолжение"
    assert relation_label(WorkRelationTypeChoices.SEQUEL, "in") == "Предыстория"


def test_relation_label_unknown_type_falls_back():
    assert relation_label("unknown", "out") == "Связано"
    assert relation_label("unknown", "in") == "Связано"


# ─── work_relation_items ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_work_relation_items_empty(book):
    assert work_relation_items(book) == []


@pytest.mark.django_db
def test_work_relation_items_outgoing(book):
    sequel = BookFactory(title="Sequel")
    rel = WorkRelationFactory(
        source=book, target=sequel, relation_type=WorkRelationTypeChoices.SEQUEL
    )

    items = work_relation_items(book)

    assert len(items) == 1
    item = items[0]
    assert set(item.keys()) == {
        "id",
        "title",
        "cover_url",
        "label",
        "icon",
        "type_key",
        "work_id",
        "relation_type",
        "direction",
    }
    assert item["id"] == rel.pk
    assert item["title"] == "Sequel"
    assert item["work_id"] == sequel.pk
    assert item["type_key"] == "book"
    assert item["direction"] == "out"
    assert item["label"] == "Продолжение"


@pytest.mark.django_db
def test_work_relation_items_incoming(book):
    prequel = BookFactory(title="Prequel")
    rel = WorkRelationFactory(
        source=prequel, target=book, relation_type=WorkRelationTypeChoices.SEQUEL
    )

    items = work_relation_items(book)

    assert len(items) == 1
    assert items[0]["id"] == rel.pk
    assert items[0]["work_id"] == prequel.pk
    assert items[0]["direction"] == "in"
    assert items[0]["label"] == "Предыстория"


@pytest.mark.django_db
def test_work_relation_items_both_directions(book):
    sequel = BookFactory()
    prequel = BookFactory()
    WorkRelationFactory(source=book, target=sequel)
    WorkRelationFactory(source=prequel, target=book)

    items = work_relation_items(book)

    assert len(items) == 2
    assert {item["direction"] for item in items} == {"out", "in"}


@pytest.mark.django_db
def test_work_relation_items_skips_dangling_target(book):
    other = BookFactory()
    rel = WorkRelationFactory(source=book, target=other)
    WorkRelation.objects.filter(pk=rel.pk).update(target_object_id=999999)

    assert work_relation_items(book) == []


@pytest.mark.django_db
def test_work_relation_items_skips_dangling_source(book):
    other = BookFactory()
    rel = WorkRelationFactory(source=other, target=book)
    WorkRelation.objects.filter(pk=rel.pk).update(source_object_id=999999)

    assert work_relation_items(book) == []
