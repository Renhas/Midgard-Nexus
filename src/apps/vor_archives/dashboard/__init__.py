from .forms import HeatmapFilterForm
from .services import (
    activity_years,
    attrs_payload,
    feed_page,
    format_number,
    format_percent,
    heat_level as _heat_level,
    heatmap_payload,
    heatmap_range,
    load_user_works,
    monday as _monday,
    percent_value,
    progress_spent,
    stats_payload,
    sunday as _sunday,
)


def parse_heatmap_year(raw):
    return HeatmapFilterForm({"year": raw}).get_year()


__all__ = [
    "_heat_level",
    "_monday",
    "_sunday",
    "activity_years",
    "attrs_payload",
    "feed_page",
    "format_number",
    "format_percent",
    "heatmap_payload",
    "heatmap_range",
    "load_user_works",
    "parse_heatmap_year",
    "percent_value",
    "progress_spent",
    "stats_payload",
]
