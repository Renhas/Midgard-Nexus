import json

from django.template import Context, Template
import pytest

from apps.vor_archives.artworks.forms import WORK_REQUIRED_FIELDS
from apps.vor_archives.constants import (
    AgeRatingChoices,
    FilmTypeChoices,
    RELATION_LABELS,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
)
from apps.vor_archives.domain import get_domain_config
from apps.vor_archives.registry import WORK_TYPES


def test_domain_config_work_types_match_registry():
    cfg = get_domain_config()
    assert cfg["workTypes"]["keys"] == list(WORK_TYPES)
    assert [item["key"] for item in cfg["workTypes"]["items"]] == list(WORK_TYPES)


def test_domain_config_statuses_and_age_ratings():
    cfg = get_domain_config()
    assert cfg["statuses"]["default"] == UserWorkStatusChoices.PLANNING
    assert cfg["statuses"]["completed"] == UserWorkStatusChoices.COMPLETED
    assert [item["value"] for item in cfg["statuses"]["options"]] == list(
        UserWorkStatusChoices.values
    )
    assert [item["value"] for item in cfg["ageRatings"]["options"]] == list(
        AgeRatingChoices.values
    )


def test_domain_config_relations_cover_all_choices():
    cfg = get_domain_config()
    rel_types = cfg["relations"]["types"]
    assert cfg["relations"]["default"] == WorkRelationTypeChoices.OTHER
    assert [item["value"] for item in rel_types] == list(WorkRelationTypeChoices.values)
    by_value = {item["value"]: item for item in rel_types}
    for rel_type, (out_label, in_label) in RELATION_LABELS.items():
        assert by_value[rel_type]["label"] == out_label
        assert by_value[rel_type]["reverseLabel"] == in_label
    assert by_value[WorkRelationTypeChoices.OTHER]["scope"] == "any"
    assert by_value[WorkRelationTypeChoices.ADAPTATION]["scope"] == "different"
    assert by_value[WorkRelationTypeChoices.SEQUEL]["scope"] == "same"


def test_domain_config_validation_rules():
    cfg = get_domain_config()
    assert cfg["validation"]["requiredByType"] == WORK_REQUIRED_FIELDS
    assert cfg["validation"]["conditionalRequired"] == [
        {
            "workType": "film",
            "when": {"filmType": FilmTypeChoices.TV_SHOW},
            "fields": ["episode_count"],
        }
    ]


@pytest.mark.parametrize(
    "section", ["workTypes", "statuses", "relations", "validation"]
)
def test_vor_domain_config_template_tag_renders_valid_json(section):
    tpl = Template("{% load vor_archives_extras %}{% vor_domain_config %}")
    rendered = tpl.render(Context({}))
    assert 'id="vor-domain-config"' in rendered
    raw_json = rendered.split(">", 1)[1].rsplit("<", 1)[0]
    parsed = json.loads(raw_json)
    assert section in parsed
