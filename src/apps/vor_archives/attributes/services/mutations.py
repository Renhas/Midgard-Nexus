from django.db import transaction

from ..catalog import SIMPLE_KINDS, genre_type_meta
from .queries import (
    genre_work_count,
    get_genre,
    get_simple_attr,
    simple_work_count,
)
from .utils import genre_composite_id, parse_genre_ids, parse_simple_ids


def _collect_delete_items(entries, resolver):
    items = []
    for entry in entries:
        item = resolver(entry)
        if item is not None:
            items.append(item)
    return items


def _resolve_genre_delete_item(pair):
    type_key, pk = pair
    obj = get_genre(type_key, pk)
    if obj is None:
        return None
    return {
        "key": genre_composite_id(type_key, pk),
        "type_key": type_key,
        "pk": pk,
        "name": obj.name,
        "type_label": genre_type_meta(type_key)["label"],
        "work_count": genre_work_count(obj, type_key),
        "obj": obj,
    }


def _resolve_simple_delete_item(kind, pk):
    obj = get_simple_attr(kind, pk)
    if obj is None:
        return None
    return {
        "key": str(pk),
        "pk": pk,
        "name": obj.name,
        "work_count": simple_work_count(obj, kind),
        "obj": obj,
    }


def build_genre_delete_items(pairs):
    return _collect_delete_items(pairs, _resolve_genre_delete_item)


def build_simple_delete_items(kind, pks):
    return _collect_delete_items(pks, lambda pk: _resolve_simple_delete_item(kind, pk))


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
