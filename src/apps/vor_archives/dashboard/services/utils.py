from datetime import date, timedelta

from apps.vor_archives.models import UserWork
from apps.vor_archives.prefetch import (
    prefetch_user_works,
    prefetch_work_relations,
)


def load_user_works(user, with_attrs: bool = False) -> list[UserWork]:
    items = list(UserWork.objects.filter(user=user).select_related("work_content_type"))
    prefetch_user_works(items)
    if with_attrs:
        prefetch_work_relations([uw.work for uw in items if uw.work], with_authors=True)
    return items


def monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def sunday(day: date) -> date:
    return day + timedelta(days=6 - day.weekday())
