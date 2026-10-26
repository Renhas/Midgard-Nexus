"""Tests for RelationsForm."""

import pytest
from apps.vor_archives.artworks.forms import RelationsForm
from apps.vor_archives.constants import WorkRelationTypeChoices


@pytest.mark.parametrize(
    "payload,expected",
    [
        pytest.param(None, [], id="missing-field"),
        pytest.param("", [], id="empty-string"),
        pytest.param("{bad", [], id="invalid-json"),
        pytest.param('"string"', [], id="not-a-list"),
        pytest.param("[1, 2]", [], id="list-of-non-dicts"),
        pytest.param(
            '[{"type_key": "book", "work_id": 5, "relation_type": "sequel"}]',
            [
                {
                    "id": None,
                    "relation_type": "sequel",
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="valid",
        ),
        pytest.param(
            '[{"type_key": "book", "work_id": 5}]',
            [
                {
                    "id": None,
                    "relation_type": WorkRelationTypeChoices.OTHER,
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="default-relation-type",
        ),
        pytest.param(
            '[{"id": "abc", "type_key": "book", "work_id": 5}]',
            [
                {
                    "id": None,
                    "relation_type": WorkRelationTypeChoices.OTHER,
                    "type_key": "book",
                    "work_id": 5,
                }
            ],
            id="invalid-id-string-to-null",
        ),
        pytest.param(
            '[{"id": 1, "work_id": "abc"}]',
            [
                {
                    "id": 1,
                    "relation_type": WorkRelationTypeChoices.OTHER,
                    "type_key": None,
                    "work_id": None,
                }
            ],
            id="invalid-work-id-string-to-null",
        ),
    ],
)
def test_relations_form(payload, expected):
    data = {} if payload is None else {"relations_json": payload}
    form = RelationsForm(data)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["relations_json"] == expected
