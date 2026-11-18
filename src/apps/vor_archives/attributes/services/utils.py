from apps.vor_archives.models import BookGenre, FilmGenre, GameGenre
from ..catalog import GENRE_TYPES


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
