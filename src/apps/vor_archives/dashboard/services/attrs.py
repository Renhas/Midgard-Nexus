from collections import Counter

from apps.vor_archives.registry import WORK_TYPES

from ..catalog import ATTR_KINDS, ATTR_VIEW_TYPES, HIST_TOP_N, TYPE_META
from .utils import load_user_works


def _attrs_to_items(user_works):
    tags = Counter()
    persons = Counter()
    platforms = Counter()
    genres = {key: Counter() for key in WORK_TYPES}

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        for tag in work.tags.all():
            tags[tag.name] += 1
        for person in work.authors.all():
            persons[person.name] += 1
        type_key = work._meta.model_name
        if type_key == "game":
            for platform in work.platforms.all():
                platforms[platform.name] += 1
        if type_key in genres and hasattr(work, "genres"):
            for genre in work.genres.all():
                genres[type_key][genre.name] += 1

    genre_items = []
    for type_key, counter in genres.items():
        for name, count in counter.items():
            genre_items.append(
                {
                    "name": f"{name} ({TYPE_META[type_key]['label']})",
                    "count": count,
                }
            )
    genre_items.sort(key=lambda item: (-item["count"], item["name"]))

    def as_items(counter):
        items = [{"name": name, "count": count} for name, count in counter.items()]
        items.sort(key=lambda item: (-item["count"], item["name"]))
        return items

    return {
        "tags": as_items(tags),
        "genres": genre_items,
        "persons": as_items(persons),
        "platforms": as_items(platforms),
    }


def attrs_payload(user):
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
