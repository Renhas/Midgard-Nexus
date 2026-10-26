"""Tests for apps.vor_archives.artworks.services.content_types."""

import pytest
from django.contrib.contenttypes.models import ContentType

from apps.vor_archives.artworks.services.content_types import ct_for, ct_for_type
from apps.vor_archives.models import Book, Film


@pytest.mark.django_db
def test_ct_for_returns_content_type(book):
    assert ct_for(book) == ContentType.objects.get_for_model(Book)


@pytest.mark.django_db
def test_ct_for_type_returns_content_type():
    assert ct_for_type("book") == ContentType.objects.get_for_model(Book)
    assert ct_for_type("film") == ContentType.objects.get_for_model(Film)


def test_ct_for_type_unknown_raises():
    with pytest.raises(KeyError):
        ct_for_type("nope")
