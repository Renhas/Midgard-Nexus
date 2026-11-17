"""Presentation helpers for work catalogs."""

from apps.vor_archives.models import (
    BookGenre,
    FilmGenre,
    GameGenre,
    Person,
    Platform,
    Tag,
)
from apps.vor_archives.registry import WORK_TYPES


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
    genre_model = {"book": BookGenre, "film": FilmGenre, "game": GameGenre}[type_key]
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
