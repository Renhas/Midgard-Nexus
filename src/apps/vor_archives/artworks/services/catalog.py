"""Presentation helpers for work catalogs and prefetching."""

from django.db.models import prefetch_related_objects

from apps.vor_archives.models import (
    BookGenre,
    FilmGenre,
    GameGenre,
    Person,
    Platform,
    Tag,
)
from apps.vor_archives.constants import WORK_TYPES


def prefetch_work(work, user_work=None):
    """Prefetch relations for a work and return its type_key."""
    type_key = work._meta.model_name
    related = ["authors", "tags", "genres"]
    if type_key == "game":
        related.append("platforms")
    prefetch_related_objects([work], *related)
    if user_work is not None:
        prefetch_related_objects([user_work], "owned_platforms")
    return type_key


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
