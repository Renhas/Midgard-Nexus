from collections.abc import Iterable

from apps.vor_archives.constants import (
    STATUS_LABELS_RU,
    UserWorkStatusChoices,
)
from apps.vor_archives.progress import progress_spent
from apps.vor_archives.registry import WORK_TYPES

from ..catalog import AGE_CHOICES_EXT, RATING_CHOICES_EXT, TYPE_META
from .utils import load_user_works


def _empty_matrix(columns: Iterable[str]) -> dict[str, dict[str, int]]:
    col_keys = tuple(columns)
    return {type_key: {col: 0 for col in col_keys} for type_key in WORK_TYPES}


def _choice_labels(choices: Iterable[tuple[str, str]]) -> dict[str, dict[str, str]]:
    return {key: {"label": label} for key, label in choices}


def stats_payload(user) -> dict:
    user_works = load_user_works(user)
    status_matrix = _empty_matrix(UserWorkStatusChoices.values)
    age_matrix = _empty_matrix(key for key, _ in AGE_CHOICES_EXT)
    rating_matrix = _empty_matrix(key for key, _ in RATING_CHOICES_EXT)
    spent = {key: 0.0 for key in WORK_TYPES}

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        type_key = work._meta.model_name
        if type_key not in WORK_TYPES:
            continue
        age_key = work.age_rating or ""
        rating_key = str(user_work.rating or "")
        age_matrix[type_key][age_key] += 1
        rating_matrix[type_key][rating_key] += 1
        status_matrix[type_key][user_work.status] += 1
        spent_row = progress_spent(user_work)
        if spent_row:
            spent[spent_row[0]] += spent_row[1]

    return {
        "stats_opts": {
            "status_matrix": status_matrix,
            "age_matrix": age_matrix,
            "rating_matrix": rating_matrix,
            "spent": spent,
            "type_meta": TYPE_META,
            "status_choices": _choice_labels(
                (key, STATUS_LABELS_RU[key]) for key in UserWorkStatusChoices.values
            ),
            "age_choices": _choice_labels(AGE_CHOICES_EXT),
            "rating_choices": _choice_labels(RATING_CHOICES_EXT),
        },
    }
