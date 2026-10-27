"""Tests for apps.vor_archives.artworks.services.catalog."""

import pytest

from apps.vor_archives.artworks.services.catalog import chip_payload
from apps.vor_archives.tests.factories import PersonFactory


# ─── chip_payload ───────────────────────────────────────────────────────────


def test_chip_payload_empty():
    assert chip_payload([]) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tip_field,expected_tip",
    [
        pytest.param("bio", "Author", id="bio-field"),
        pytest.param("missing_attr", "", id="missing-attr"),
    ],
)
def test_chip_payload_person(tip_field, expected_tip):
    person = PersonFactory(name="Tolkien", bio="Author")
    assert chip_payload([person], tip_field) == [
        {"id": person.pk, "name": "Tolkien", "tip": expected_tip}
    ]
