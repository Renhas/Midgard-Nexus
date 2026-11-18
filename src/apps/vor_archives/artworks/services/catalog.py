"""Presentation helpers for work catalogs."""

from apps.vor_archives.models import (
    Person,
    Platform,
    Tag,
)
from apps.vor_archives.registry import GENRE_MODELS, WORK_TYPES


def chip_payload(items, tip_field="description"):
    return [
        {
            "id": item.pk,
            "name": item.name,
            "tip": getattr(item, tip_field, "") or "",
        }
        for item in items
    ]


def attr_catalog(type_key):
    genre_model = GENRE_MODELS[type_key]
    return {
        "authors": chip_payload(Person.objects.order_by("name"), "bio"),
        "genres": chip_payload(genre_model.objects.order_by("name")),
        "tags": chip_payload(Tag.objects.order_by("name")),
        "platforms": chip_payload(Platform.objects.order_by("name"), "")
        if type_key == "game"
        else [],
    }


def all_attr_catalogs():
    return {key: attr_catalog(key) for key in WORK_TYPES}
