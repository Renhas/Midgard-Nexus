from collections.abc import Callable

from django.http import QueryDict

from .activity import (
    activity_context,
    activity_years,
    feed_context,
    feed_page,
    heat_level,
    heatmap_payload,
    heatmap_range,
)
from .attrs import attrs_payload
from .stats import progress_spent, stats_payload
from .utils import (
    load_user_works,
    monday,
    sunday,
)

TabContextBuilder = Callable[[object, QueryDict], dict]

TAB_CONTEXT_BUILDERS: dict[str, TabContextBuilder] = {
    "stats": lambda user, _params: stats_payload(user),
    "attrs": lambda user, _params: attrs_payload(user),
    "activity": activity_context,
}

__all__ = [
    "TAB_CONTEXT_BUILDERS",
    "activity_context",
    "activity_years",
    "attrs_payload",
    "feed_context",
    "feed_page",
    "heat_level",
    "heatmap_payload",
    "heatmap_range",
    "load_user_works",
    "monday",
    "progress_spent",
    "stats_payload",
    "sunday",
]
