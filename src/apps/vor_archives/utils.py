"""Shared helpers across vor_archives pages."""

from django.conf import settings


def module_context() -> dict:
    """Return shared template metadata for the vor_archives module."""
    return next(m for m in settings.MODULES if m["url_name"] == "vor_archives")


def module_base_context(active_section: str, *, hide_right: bool = False) -> dict:
    """Return common shell template variables for vor_archives pages."""
    module = module_context()
    context = {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_color": module["color"],
        "active_section": active_section,
    }
    if hide_right:
        context["hide_right"] = True
    return context


def parse_int_list(
    raw_values,
    *,
    comma_separated: bool = False,
    unique: bool = False,
) -> list[int]:
    """Parse raw string values into a list of ints.

    Empty and non-numeric entries are skipped silently. When
    comma_separated is True, each raw value is split on commas first.
    When unique is True, duplicates are removed while preserving order.
    """
    result = []
    seen = set()
    for raw in raw_values:
        parts = str(raw).split(",") if comma_separated else [str(raw)]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                value = int(part)
            except (TypeError, ValueError):
                continue
            if unique:
                if value in seen:
                    continue
                seen.add(value)
            result.append(value)
    return result
