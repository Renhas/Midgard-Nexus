"""Work progress metadata and clamping helpers."""

from decimal import Decimal
from typing import NamedTuple

from apps.vor_archives.constants import FilmTypeChoices
from apps.vor_archives.registry import WORK_TYPE_UNITS

MINUTES_PER_HOUR = 60.0


class ProgressMeta(NamedTuple):
    maximum: int | None
    unit: str
    step: float
    max_field: str | None = None


class SubtypedProgressRules(NamedTuple):
    subtype_field: str
    rules: dict[str, ProgressMeta]


PROGRESS_RULES: dict[str, ProgressMeta | SubtypedProgressRules] = {
    "book": ProgressMeta(maximum=None, unit="стр.", step=1, max_field="pages"),
    "game": ProgressMeta(maximum=None, unit="ч.", step=0.5, max_field=None),
    "film": SubtypedProgressRules(
        subtype_field="film_type",
        rules={
            str(FilmTypeChoices.MOVIE): ProgressMeta(
                maximum=None, unit="мин.", step=1, max_field="duration_minutes"
            ),
            str(FilmTypeChoices.TV_SHOW): ProgressMeta(
                maximum=None, unit="эп.", step=1, max_field="episode_count"
            ),
        },
    ),
}


def iter_progress_rules():
    """Yield ``(type_key, subtype_field, subtype_value, ProgressMeta)`` entries."""
    for type_key, entry in PROGRESS_RULES.items():
        if isinstance(entry, SubtypedProgressRules):
            for subtype, meta in entry.rules.items():
                yield type_key, entry.subtype_field, subtype, meta
        else:
            yield type_key, None, None, entry


def resolve_progress_rule(work) -> ProgressMeta | None:
    """Return declarative ProgressMeta template for a work instance."""
    entry = PROGRESS_RULES.get(work._meta.model_name)
    if isinstance(entry, SubtypedProgressRules):
        subtype = getattr(work, entry.subtype_field, None)
        return entry.rules.get(str(subtype))
    return entry


def work_progress(work) -> ProgressMeta:
    """Return progress metadata for a work instance (Book, Film, or Game)."""
    if work is None:
        return ProgressMeta(maximum=None, unit="", step=1)
    rule = resolve_progress_rule(work)
    if rule is None:
        return ProgressMeta(maximum=None, unit="", step=1)
    maximum = getattr(work, rule.max_field or "", None)
    return ProgressMeta(maximum=maximum, unit=rule.unit, step=rule.step)


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


def _film_spent_hours(work, progress: float) -> float:
    if work.film_type == FilmTypeChoices.TV_SHOW:
        duration = float(work.duration_minutes or 0)
        return duration * progress / MINUTES_PER_HOUR
    return progress / MINUTES_PER_HOUR


def progress_spent(user_work) -> tuple[str, float, str] | None:
    """Return ``(type_key, spent_amount, unit)`` for a UserWork."""
    work = getattr(user_work, "work", None)
    if work is None:
        return None
    type_key = work._meta.model_name
    unit = WORK_TYPE_UNITS.get(type_key)
    if unit is None:
        return None
    progress = float(user_work.progress or 0)
    amount = _film_spent_hours(work, progress) if type_key == "film" else progress
    return (type_key, amount, unit)
