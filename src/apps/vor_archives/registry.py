"""Registry of work models and type-key lookup helpers."""

from .models import Book, Film, Game

WORK_MODELS = {
    "book": Book,
    "film": Film,
    "game": Game,
}


def get_work_model(type_key: str):
    try:
        return WORK_MODELS[type_key]
    except KeyError:
        raise ValueError(f"Unknown work type: {type_key}")
