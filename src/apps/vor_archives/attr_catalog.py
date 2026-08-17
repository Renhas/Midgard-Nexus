from django.db.models import Count

from .models import BookGenre, FilmGenre, GameGenre

ATTR_TABS = [
    {"kind": "tags", "label": "Теги", "icon": "bi bi-tag", "ready": False},
    {"kind": "persons", "label": "Авторы", "icon": "bi bi-person", "ready": False},
    {"kind": "genres", "label": "Жанры", "icon": "bi bi-bookmark", "ready": True},
    {"kind": "platforms", "label": "Платформы", "icon": "bi bi-controller", "ready": False},
]

DEFAULT_KIND = "genres"

GENRE_TYPES = {
    "book": {"model": BookGenre, "label": "Книги", "count_field": "book"},
    "film": {"model": FilmGenre, "label": "Фильмы", "count_field": "film"},
    "game": {"model": GameGenre, "label": "Игры", "count_field": "game"},
}

ATTR_KIND_MAP = {tab["kind"]: tab for tab in ATTR_TABS}


def get_attr_tab(kind):
    return ATTR_KIND_MAP.get(kind)


def genre_type_meta(type_key):
    return GENRE_TYPES.get(type_key)


def genre_type_key(obj):
    if isinstance(obj, BookGenre):
        return "book"
    if isinstance(obj, FilmGenre):
        return "film"
    if isinstance(obj, GameGenre):
        return "game"
    raise ValueError(f"Unknown genre model: {obj!r}")


def genre_composite_id(type_key, pk):
    return f"{type_key}:{pk}"


def parse_genre_ids(raw_values):
    parsed = []
    seen = set()
    for raw in raw_values:
        for part in str(raw).split(","):
            part = part.strip()
            if ":" not in part:
                continue
            type_key, pk_raw = part.split(":", 1)
            if type_key not in GENRE_TYPES:
                continue
            try:
                pk = int(pk_raw)
            except (TypeError, ValueError):
                continue
            key = (type_key, pk)
            if key in seen:
                continue
            seen.add(key)
            parsed.append(key)
    return parsed


def get_genre(type_key, pk):
    meta = genre_type_meta(type_key)
    if meta is None:
        return None
    return meta["model"].objects.filter(pk=pk).first()


def genre_work_count(obj, type_key=None):
    type_key = type_key or genre_type_key(obj)
    accessor = f"{GENRE_TYPES[type_key]['count_field']}_set"
    return getattr(obj, accessor).count()


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
        groups.append({
            "type_key": type_key,
            "label": meta["label"],
            "items": items,
        })
    return groups, total
