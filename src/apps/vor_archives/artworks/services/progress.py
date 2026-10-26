"""Work progress metadata and clamping services."""

from decimal import Decimal
from typing import NamedTuple

from apps.vor_archives.constants import FilmTypeChoices


class ProgressMeta(NamedTuple):
    maximum: int | None
    unit: str
    step: float


def work_progress(work) -> ProgressMeta:
    """Return progress metadata for a work instance (Book, Film, or Game)."""
    if work is None:
        return ProgressMeta(maximum=None, unit="", step=1)
    model_name = work._meta.model_name
    if model_name == "book":
        return ProgressMeta(maximum=work.pages, unit="стр.", step=1)
    if model_name == "game":
        return ProgressMeta(maximum=None, unit="ч.", step=0.5)
    if model_name == "film":
        if work.film_type == FilmTypeChoices.TV_SHOW:
            return ProgressMeta(maximum=work.episode_count, unit="эп.", step=1)
        return ProgressMeta(maximum=work.duration_minutes, unit="мин.", step=1)
    return ProgressMeta(maximum=None, unit="", step=1)


def user_work_progress(user_work) -> ProgressMeta:
    """Return progress metadata for a UserWork based on its work type."""
    if user_work is None:
        return ProgressMeta(maximum=None, unit="", step=1)
    return work_progress(getattr(user_work, "work", None))


def display_progress_value(value) -> str:
    """Format a progress value for display: integer when whole, else one decimal."""
    number = float(value or 0)
    rounded = round(number, 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def get_progress_info(user_work) -> dict | None:
    """Return a template-ready progress info dict for a UserWork.

    Returns None when user_work or its related work is missing.
    """
    if not user_work or not getattr(user_work, "work", None):
        return None
    meta = work_progress(user_work.work)
    return {
        "value": float(user_work.progress or 0),
        "display_value": display_progress_value(user_work.progress),
        "maximum": meta.maximum,
        "unit": meta.unit,
        "step": meta.step,
    }


def clamp_progress(user_work) -> Decimal:
    """Clamp user_work.progress to its work maximum. Does not save."""
    meta = user_work_progress(user_work)
    if meta.maximum is None:
        return user_work.progress
    limit = Decimal(str(meta.maximum))
    if user_work.progress > limit:
        user_work.progress = limit
    return user_work.progress


def clamp_progress_for_work(work) -> None:
    """Clamp progress of every UserWork linked to work to its maximum."""
    meta = work_progress(work)
    if meta.maximum is None:
        return
    limit = Decimal(str(meta.maximum))
    for user_work in work.user_works.all():
        if user_work.progress > limit:
            user_work.progress = limit
            user_work.save()
