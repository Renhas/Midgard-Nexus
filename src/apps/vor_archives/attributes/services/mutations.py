from django.db import transaction

from ..catalog import SIMPLE_KINDS, genre_type_meta
from .queries import (
    genre_work_count,
    get_genre,
    get_simple_attr,
    simple_work_count,
)
from .utils import genre_composite_id, parse_genre_ids, parse_simple_ids


def build_genre_delete_items(pairs):
    items = []
    for type_key, pk in pairs:
        obj = get_genre(type_key, pk)
        if obj is None:
            continue
        items.append(
            {
                "key": genre_composite_id(type_key, pk),
                "type_key": type_key,
                "pk": pk,
                "name": obj.name,
                "type_label": genre_type_meta(type_key)["label"],
                "work_count": genre_work_count(obj, type_key),
                "obj": obj,
            }
        )
    return items


def build_simple_delete_items(kind, pks):
    items = []
    for pk in pks:
        obj = get_simple_attr(kind, pk)
        if obj is None:
            continue
        items.append(
            {
                "key": str(pk),
                "pk": pk,
                "name": obj.name,
                "work_count": simple_work_count(obj, kind),
                "obj": obj,
            }
        )
    return items


def resolve_delete_items(kind, raw_ids):
    if kind == "genres":
        return build_genre_delete_items(parse_genre_ids(raw_ids))
    if kind in SIMPLE_KINDS:
        return build_simple_delete_items(kind, parse_simple_ids(raw_ids))
    raise ValueError(f"Unknown attribute kind: {kind}")


@transaction.atomic
def delete_attrs(kind, raw_ids):
    items = resolve_delete_items(kind, raw_ids)
    for item in items:
        item["obj"].delete()
    return len(items)
