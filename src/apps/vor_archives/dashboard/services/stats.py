from apps.vor_archives.constants import (
    FilmTypeChoices,
    STATUS_LABELS_RU,
    UserWorkStatusChoices,
)
from apps.vor_archives.registry import WORK_TYPES

from ..catalog import AGE_CHOICES_EXT, RATING_CHOICES_EXT, TYPE_META
from .utils import load_user_works


def progress_spent(user_work):
    work = getattr(user_work, "work", None)
    if work is None:
        return None
    progress = float(user_work.progress or 0)
    model_name = work._meta.model_name
    if model_name == "book":
        return ("book", progress, "стр.")
    if model_name == "game":
        return ("game", progress, "ч.")
    if model_name == "film":
        if work.film_type == FilmTypeChoices.TV_SHOW:
            duration = float(work.duration_minutes or 0)
            return ("film", duration * progress / 60.0, "ч.")
        return ("film", progress / 60.0, "ч.")
    return None


def _empty_status_matrix():
    return {
        type_key: {status: 0 for status in UserWorkStatusChoices.values}
        for type_key in WORK_TYPES
    }


def _empty_age_matrix():
    return {type_key: {age[0]: 0 for age in AGE_CHOICES_EXT} for type_key in WORK_TYPES}


def _empty_rating_matrix():
    return {
        type_key: {rat[0]: 0 for rat in RATING_CHOICES_EXT} for type_key in WORK_TYPES
    }


def stats_payload(user):
    user_works = load_user_works(user)
    status_matrix = _empty_status_matrix()
    age_matrix = _empty_age_matrix()
    rating_matrix = _empty_rating_matrix()
    spent = {key: 0.0 for key in WORK_TYPES}

    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        type_key = work._meta.model_name
        age_key = work.age_rating or ""
        rating_key = str(user_work.rating or "")
        if type_key not in WORK_TYPES:
            continue
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
            "status_choices": {
                key: {"label": STATUS_LABELS_RU[key]}
                for key in UserWorkStatusChoices.values
            },
            "age_choices": {key: {"label": name} for key, name in AGE_CHOICES_EXT},
            "rating_choices": {
                key: {"label": name} for key, name in RATING_CHOICES_EXT
            },
        },
    }
