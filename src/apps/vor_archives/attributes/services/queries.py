from functools import reduce
from operator import add

from django.db.models import Count

from ..catalog import GENRE_TYPES, SIMPLE_KINDS, genre_type_meta
from .utils import genre_composite_id, genre_type_key


def get_genre(type_key, pk):
    meta = genre_type_meta(type_key)
    if meta is None:
        return None
    return meta["model"].objects.filter(pk=pk).first()


def get_simple_attr(kind, pk):
    meta = SIMPLE_KINDS.get(kind)
    if meta is None:
        return None
    return meta["model"].objects.filter(pk=pk).first()


def genre_work_count(obj, type_key=None):
    type_key = type_key or genre_type_key(obj)
    accessor = f"{GENRE_TYPES[type_key]['count_field']}_set"
    return getattr(obj, accessor).count()


def simple_work_count(obj, kind):
    meta = SIMPLE_KINDS[kind]
    return sum(getattr(obj, f"{field}_set").count() for field in meta["count_fields"])


def list_genre_groups(query=""):
    query = (query or "").strip()
    groups = []
    total = 0
    for type_key, meta in GENRE_TYPES.items():
        total += meta["model"].objects.count()
        qs = meta["model"].objects.annotate(
            work_count=Count(meta["count_field"], distinct=True)
        )
        if query:
            qs = qs.filter(name__icontains=query)
        items = [
            {
                "key": genre_composite_id(type_key, obj.pk),
                "pk": obj.pk,
                "type_key": type_key,
                "name": obj.name,
                "work_count": obj.work_count,
            }
            for obj in qs.order_by("name")
        ]
        groups.append(
            {
                "type_key": type_key,
                "label": meta["label"],
                "items": items,
            }
        )
    return groups, total


def list_simple_attrs(kind, query=""):
    meta = SIMPLE_KINDS[kind]
    query = (query or "").strip()
    total = meta["model"].objects.count()
    counts = [Count(field, distinct=True) for field in meta["count_fields"]]
    qs = meta["model"].objects.annotate(work_count=reduce(add, counts))
    if query:
        qs = qs.filter(name__icontains=query)
    items = [
        {
            "key": str(obj.pk),
            "pk": obj.pk,
            "name": obj.name,
            "work_count": obj.work_count,
        }
        for obj in qs.order_by("name")
    ]
    return items, total
