from apps.vor_archives.registry import GENRE_MODELS, GENRE_TYPE_BY_MODEL
from apps.vor_archives.utils import parse_int_list


def genre_type_key(obj):
    type_key = GENRE_TYPE_BY_MODEL.get(type(obj))
    if type_key is None:
        raise ValueError(f"Unknown genre model: {obj!r}")
    return type_key


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
            if type_key not in GENRE_MODELS:
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
    return parse_int_list(raw_values, comma_separated=True, unique=True)
