from functools import reduce
from operator import add

from django.db.models import Count

from .models import BookGenre, FilmGenre, GameGenre, Person, Platform, Tag

ATTR_TABS = [
    {
        "kind": "tags",
        "label": "Теги",
        "icon": "bi bi-tag",
        "search_placeholder": "Поиск тега",
        "count_label": "Тегов",
        "empty_prompt": "Выберите тег из списка",
        "none_yet": "Тегов пока нет",
        "create_title": "Новый тег",
        "noun_one": "тег",
        "noun_many": "теги",
        "delete_one": "Тег «{name}» будет удалён.",
        "delete_many": "Выбранные теги ({count}) будут удалены.",
    },
    {
        "kind": "persons",
        "label": "Авторы",
        "icon": "bi bi-person",
        "search_placeholder": "Поиск автора",
        "count_label": "Авторов",
        "empty_prompt": "Выберите автора из списка",
        "none_yet": "Авторов пока нет",
        "create_title": "Новый автор",
        "noun_one": "автор",
        "noun_many": "авторы",
        "delete_one": "Автор «{name}» будет удалён.",
        "delete_many": "Выбранные авторы ({count}) будут удалены.",
    },
    {
        "kind": "genres",
        "label": "Жанры",
        "icon": "icon-drama",
        "search_placeholder": "Поиск жанра",
        "count_label": "Жанров",
        "empty_prompt": "Выберите жанр из списка",
        "none_yet": "Жанров пока нет",
        "create_title": "Новый жанр",
        "noun_one": "жанр",
        "noun_many": "жанры",
        "delete_one": "Жанр «{name}» будет удалён.",
        "delete_many": "Выбранные жанры ({count}) будут удалены.",
    },
    {
        "kind": "platforms",
        "label": "Платформы",
        "icon": "bi bi-controller",
        "search_placeholder": "Поиск платформы",
        "count_label": "Платформ",
        "empty_prompt": "Выберите платформу из списка",
        "none_yet": "Платформ пока нет",
        "create_title": "Новая платформа",
        "noun_one": "платформа",
        "noun_many": "платформы",
        "delete_one": "Платформа «{name}» будет удалена.",
        "delete_many": "Выбранные платформы ({count}) будут удалены.",
    },
]

DEFAULT_KIND = "tags"

GENRE_TYPES = {
    "book": {"model": BookGenre, "label": "Книги", "count_field": "book"},
    "film": {"model": FilmGenre, "label": "Фильмы", "count_field": "film"},
    "game": {"model": GameGenre, "label": "Игры", "count_field": "game"},
}

SIMPLE_KINDS = {
    "tags": {
        "model": Tag,
        "name_label": "Название",
        "text_field": "description",
        "text_label": "Описание",
        "count_fields": ("book", "film", "game"),
        "unique_error": "Тег с таким названием уже существует",
        "empty_text": "Нет описания",
    },
    "persons": {
        "model": Person,
        "name_label": "Имя",
        "text_field": "bio",
        "text_label": "Биография",
        "count_fields": ("book", "film", "game"),
        "unique_error": "Автор с таким именем уже существует",
        "empty_text": "Нет биографии",
    },
    "platforms": {
        "model": Platform,
        "name_label": "Название",
        "text_field": None,
        "text_label": None,
        "count_fields": ("game",),
        "unique_error": "Платформа с таким названием уже существует",
    },
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


def parse_simple_ids(raw_values):
    parsed = []
    seen = set()
    for raw in raw_values:
        for part in str(raw).split(","):
            part = part.strip()
            try:
                pk = int(part)
            except (TypeError, ValueError):
                continue
            if pk in seen:
                continue
            seen.add(pk)
            parsed.append(pk)
    return parsed


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
        groups.append({
            "type_key": type_key,
            "label": meta["label"],
            "items": items,
        })
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
