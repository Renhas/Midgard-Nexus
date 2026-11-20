from datetime import timedelta

from apps.vor_archives.models import UserWork
from apps.vor_archives.prefetch import (
    prefetch_user_works,
    prefetch_work_relations,
)


def format_number(value):
    number = round(float(value or 0), 1)
    if number == int(number):
        return str(int(number))
    return str(number)


def format_percent(part, total):
    if not total:
        return "0%"
    value = round(part * 100 / total, 1)
    if value == int(value):
        return f"{int(value)}%"
    return f"{value}%"


def percent_value(part, total):
    if not total:
        return 0
    return round(part * 100 / total, 1)


def load_user_works(user, with_attrs=False):
    items = list(UserWork.objects.filter(user=user).select_related("work_content_type"))
    prefetch_user_works(items)
    if with_attrs:
        prefetch_work_relations([uw.work for uw in items if uw.work], with_authors=True)
    return items


def monday(day):
    return day - timedelta(days=day.weekday())


def sunday(day):
    return day + timedelta(days=6 - day.weekday())
