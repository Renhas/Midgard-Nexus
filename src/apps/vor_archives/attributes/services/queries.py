from functools import reduce
from operator import add

from django.db.models import Count

from ..catalog import GENRE_TYPES, SIMPLE_KINDS, genre_type_meta
from .utils import genre_composite_id, genre_type_key


def _annotate_work_count(model, count_fields):
    counts = [Count(field, distinct=True) for field in count_fields]
    return model.objects.annotate(work_count=reduce(add, counts))


def _count_linked_works(obj, count_fields):
    return sum(getattr(obj, f"{field}_set").count() for field in count_fields)


def _list_model_items(model, count_fields, query="", *, extra_fields=None):
    query = (query or "").strip()
    total = model.objects.count()
    qs = _annotate_work_count(model, count_fields)
    if query:
        qs = qs.filter(name__icontains=query)
    items = []
    for obj in qs.order_by("name"):
        extra = extra_fields(obj) if extra_fields else {}
        items.append(
            {
                "key": extra.get("key", str(obj.pk)),
                "pk": obj.pk,
                "name": obj.name,
                "work_count": obj.work_count,
                **extra,
            }
        )
    return items, total


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
    return _count_linked_works(obj, (GENRE_TYPES[type_key]["count_field"],))


def simple_work_count(obj, kind):
    return _count_linked_works(obj, SIMPLE_KINDS[kind]["count_fields"])


def list_genre_groups(query=""):
    groups = []
    total = 0
    for type_key, meta in GENRE_TYPES.items():
        items, group_total = _list_model_items(
            meta["model"],
            (meta["count_field"],),
            query,
            extra_fields=lambda obj, tk=type_key: {
                "key": genre_composite_id(tk, obj.pk),
                "type_key": tk,
            },
        )
        total += group_total
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
    return _list_model_items(meta["model"], meta["count_fields"], query)
