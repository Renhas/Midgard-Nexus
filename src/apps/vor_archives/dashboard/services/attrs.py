from collections import Counter

from apps.vor_archives.registry import ATTRIBUTE_KIND_REGISTRY, WORK_TYPES

from ..catalog import ATTR_KINDS, ATTR_VIEW_TYPES, HIST_TOP_N, TYPE_META
from .utils import load_user_works


def _counter_to_sorted_items(counter: Counter[str]) -> list[dict[str, int | str]]:
    items: list[dict[str, int | str]] = [
        {"name": name, "count": count} for name, count in counter.items()
    ]
    items.sort(key=lambda item: (-item["count"], item["name"]))
    return items


def _attrs_to_items(user_works) -> dict[str, list[dict[str, int | str]]]:
    tags: Counter[str] = Counter()
    persons: Counter[str] = Counter()
    platforms: Counter[str] = Counter()
    genres: dict[str, Counter[str]] = {key: Counter() for key in WORK_TYPES}

    platform_work_types = ATTRIBUTE_KIND_REGISTRY["platforms"].work_types
    genre_work_types = ATTRIBUTE_KIND_REGISTRY["genres"].work_types

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        type_key = work._meta.model_name
        tags.update(tag.name for tag in work.tags.all())
        persons.update(person.name for person in work.authors.all())
        if type_key in platform_work_types:
            platforms.update(platform.name for platform in work.platforms.all())
        if type_key in genre_work_types and type_key in genres:
            genres[type_key].update(genre.name for genre in work.genres.all())

    genre_counter: Counter[str] = Counter()
    for type_key, counter in genres.items():
        type_label = TYPE_META[type_key]["label"]
        for name, count in counter.items():
            genre_counter[f"{name} ({type_label})"] = count

    return {
        "tags": _counter_to_sorted_items(tags),
        "genres": _counter_to_sorted_items(genre_counter),
        "persons": _counter_to_sorted_items(persons),
        "platforms": _counter_to_sorted_items(platforms),
    }


def attrs_payload(user) -> dict:
    user_works = load_user_works(user, with_attrs=True)
    return {
        "attr_kinds": ATTR_KINDS,
        "view_types": ATTR_VIEW_TYPES,
        "attrs_opts": {
            "attrs": _attrs_to_items(user_works),
            "total": len(user_works),
            "histTopN": HIST_TOP_N,
        },
    }
