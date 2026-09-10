"""Tests for apps.vor_archives validators."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from apps.vor_archives.constants import WorkRelationTypeChoices
from apps.vor_archives.models import Book
from apps.vor_archives.tests.factories import BookFactory, FilmFactory, GameFactory
from apps.vor_archives.validators import (
    CycleChecker,
    validate_gfk,
    validate_relation_type,
)

A = (1, 1)
B = (1, 2)
C = (1, 3)
D = (1, 4)


def _adj(edges):
    graph = {}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)
    return lambda key: graph.get(key, ())


@pytest.mark.parametrize(
    ("ct", "obj_id"),
    [
        (None, None),
        (None, 1),
        ("book_ct", None),
    ],
)
@pytest.mark.django_db
def test_validate_gfk_skips_when_ct_or_id_missing(ct, obj_id, book):
    if ct == "book_ct":
        ct = ContentType.objects.get_for_model(Book)
    validate_gfk(ct, obj_id)


@pytest.mark.django_db
def test_validate_gfk_accepts_existing_object(book):
    validate_gfk(ContentType.objects.get_for_model(Book), book.pk)


@pytest.mark.django_db
@pytest.mark.parametrize("missing_id", [0, 999_999])
def test_validate_gfk_rejects_missing_object(book, missing_id):
    ct = ContentType.objects.get_for_model(Book)
    with pytest.raises(ValidationError):
        validate_gfk(ct, missing_id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("source_factory", "target_factory", "relation_type"),
    [
        (BookFactory, BookFactory, WorkRelationTypeChoices.OTHER),
        (BookFactory, FilmFactory, WorkRelationTypeChoices.OTHER),
        (BookFactory, FilmFactory, WorkRelationTypeChoices.ADAPTATION),
        (FilmFactory, GameFactory, WorkRelationTypeChoices.ADAPTATION),
        (BookFactory, BookFactory, WorkRelationTypeChoices.SEQUEL),
        (FilmFactory, FilmFactory, WorkRelationTypeChoices.SPIN_OFF),
        (BookFactory, BookFactory, WorkRelationTypeChoices.REMAKE),
    ],
)
def test_validate_relation_type_allows_valid_pairs(
    source_factory, target_factory, relation_type
):
    source = source_factory()
    target = target_factory()
    validate_relation_type(
        ContentType.objects.get_for_model(source),
        ContentType.objects.get_for_model(target),
        relation_type,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("source_factory", "target_factory", "relation_type"),
    [
        (BookFactory, BookFactory, WorkRelationTypeChoices.ADAPTATION),
        (BookFactory, FilmFactory, WorkRelationTypeChoices.SEQUEL),
        (BookFactory, FilmFactory, WorkRelationTypeChoices.SPIN_OFF),
        (BookFactory, FilmFactory, WorkRelationTypeChoices.REMAKE),
    ],
)
def test_validate_relation_type_rejects_invalid_pairs(
    source_factory, target_factory, relation_type
):
    source = source_factory()
    target = target_factory()
    with pytest.raises(ValidationError):
        validate_relation_type(
            ContentType.objects.get_for_model(source),
            ContentType.objects.get_for_model(target),
            relation_type,
        )


def test_cycle_checker_self_loop():
    checker = CycleChecker(items_out=_adj([]), items_in=_adj([]))
    assert checker.check(A, A) is True


def test_cycle_checker_empty_graph_distinct_nodes():
    checker = CycleChecker(items_out=_adj([]), items_in=_adj([]))
    assert checker.check(A, B) is False


def test_cycle_checker_direct_outgoing_edge():
    checker = CycleChecker(items_out=_adj([(A, B)]), items_in=_adj([]))
    assert checker.check(A, B) is True
    assert checker.check(B, A) is False


def test_cycle_checker_outgoing_chain():
    checker = CycleChecker(items_out=_adj([(A, B), (B, C)]), items_in=_adj([]))
    assert checker.check(A, C) is True
    assert checker.check(A, D) is False


def test_cycle_checker_incoming_edge():
    checker = CycleChecker(items_out=_adj([]), items_in=_adj([(B, A)]))
    assert checker.check(B, A) is True


def test_cycle_checker_mix_outgoing_and_incoming():
    checker = CycleChecker(items_out=_adj([(C, B)]), items_in=_adj([(B, A)]))
    assert checker.check(C, A) is True
