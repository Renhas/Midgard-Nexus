"""Single-field updates to UserWork from the quick actions UI."""

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, NamedTuple

from apps.vor_archives.constants import UserWorkStatusChoices

from .progress import user_work_progress

if TYPE_CHECKING:
    from apps.vor_archives.models import UserWork


class QuickField(NamedTuple):
    label: str
    handler: Callable[["UserWork", Any], dict]


class PlatformNotRelated(Exception):
    """Raised when a platform to toggle is not linked to the UserWork's work."""


def quick_update(user_work, field, value):
    """Apply a single-field update to a UserWork.

    Returns a JSON-ready payload. Callers must pass field/value already
    parsed by QuickUpdateForm. Raises PlatformNotRelated for owned_platform.
    """
    spec = QUICK_UPDATE_FIELDS.get(field)
    if spec is None:
        raise ValueError(f"Unknown quick-update field: {field}")
    return spec.handler(user_work, value)


def _apply_status(user_work, value):
    old_status = user_work.status
    user_work.status = value
    meta = user_work_progress(user_work)
    if value == UserWorkStatusChoices.COMPLETED:
        if meta.maximum is not None:
            user_work.progress = Decimal(str(meta.maximum))
    elif value == UserWorkStatusChoices.IN_PROGRESS:
        if old_status in (
            UserWorkStatusChoices.COMPLETED,
            UserWorkStatusChoices.DROPPED,
        ):
            user_work.progress = Decimal("0")
    user_work.save()
    return _standard_payload(user_work)


def _apply_progress(user_work, value):
    meta = user_work_progress(user_work)
    progress = value
    if meta.maximum is not None:
        maximum = Decimal(str(meta.maximum))
        progress = min(progress, maximum)
        if progress >= maximum:
            user_work.status = UserWorkStatusChoices.COMPLETED
    user_work.progress = progress
    user_work.save()
    return _standard_payload(user_work)


def _apply_rating(user_work, value):
    user_work.rating = value
    user_work.save()
    return _standard_payload(user_work)


def _apply_is_hidden(user_work, value):
    user_work.is_hidden = value
    user_work.save()
    return _standard_payload(user_work)


def _apply_times_completed(user_work, value):
    user_work.times_completed = value
    user_work.save()
    return _standard_payload(user_work)


def _apply_owned_platform(user_work, value):
    work = user_work.work
    if work is None or not work.platforms.filter(pk=value).exists():
        raise PlatformNotRelated()
    if user_work.owned_platforms.filter(pk=value).exists():
        user_work.owned_platforms.remove(value)
    else:
        user_work.owned_platforms.add(value)
    return {
        "owned_platform_ids": list(
            user_work.owned_platforms.values_list("pk", flat=True)
        ),
    }


def _standard_payload(user_work):
    return {
        "status": user_work.status,
        "progress": float(user_work.progress or 0),
        "times_completed": user_work.times_completed,
        "last_completed_date": (
            user_work.last_completed_date.strftime("%d.%m.%Y")
            if user_work.last_completed_date
            else ""
        ),
    }


QUICK_UPDATE_FIELDS: dict[str, QuickField] = {
    "status": QuickField("Статус", _apply_status),
    "progress": QuickField("Прогресс", _apply_progress),
    "rating": QuickField("Рейтинг", _apply_rating),
    "is_hidden": QuickField("Скрыто", _apply_is_hidden),
    "times_completed": QuickField("Завершений", _apply_times_completed),
    "owned_platform": QuickField("Платформа", _apply_owned_platform),
}
