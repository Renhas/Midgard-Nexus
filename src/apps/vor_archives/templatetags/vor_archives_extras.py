from django import template

from ..constants import FilmTypeChoices

register = template.Library()


WORK_TYPE_ICONS = {
    "book": "icon-book-text",
    "film": "icon-clapperboard",
    "game": "icon-gamepad-2",
}

WORK_TYPE_LABELS = {
    "book": "Книга",
    "film": "Фильм",
    "game": "Игра",
}

STATUS_LABELS_RU = {
    "planning": "Запланировано",
    "in_progress": "В процессе",
    "completed": "Завершено",
    "dropped": "Брошено",
}

STATUS_ICONS = {
    "planning": "bi bi-clock-fill",
    "in_progress": "bi bi-play-circle-fill",
    "completed": "bi bi-check-circle-fill",
    "dropped": "bi bi-x-circle-fill",
}

FEED_ACTION_LABELS_RU = {
    "added": "Добавлено",
    "planning": "Запланировано",
    "in_progress": "В процессе",
    "completed": "Завершено",
    "dropped": "Брошено",
    "rated": "Оценка",
}

FEED_ACTION_ICONS = {
    "added": "bi bi-plus-circle",
    "planning": "bi bi-clock",
    "in_progress": "bi bi-play-circle",
    "completed": "bi bi-check-circle",
    "dropped": "bi bi-x-circle",
    "rated": "bi bi-star",
}


def _display_progress_value(value):
    number = float(value or 0)
    rounded = round(number, 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def get_progress_info(user_work):
    if not user_work or not getattr(user_work, "work", None):
        return None
    work = user_work.work
    model_name = work._meta.model_name
    info = {
        "value": float(user_work.progress or 0),
        "display_value": _display_progress_value(user_work.progress),
        "maximum": None,
        "unit": "",
        "step": 1,
    }
    if model_name == "book":
        info["maximum"] = work.pages
        info["unit"] = "стр."
    elif model_name == "game":
        info["unit"] = "ч."
        info["step"] = 0.5
    elif model_name == "film":
        if work.film_type == FilmTypeChoices.TV_SHOW:
            info["maximum"] = work.episode_count
            info["unit"] = "эп."
        else:
            info["maximum"] = work.duration_minutes
            info["unit"] = "мин."
    return info


@register.filter
def get_model_icon(obj):
    if not obj:
        return "bi bi-collection"
    return WORK_TYPE_ICONS.get(obj._meta.model_name, "bi bi-collection")


@register.filter
def get_work_type_icon(user_work):
    if not user_work or not hasattr(user_work, "work"):
        return ""
    return get_model_icon(user_work.work)


@register.filter
def format_progress(user_work):
    info = get_progress_info(user_work)
    if not info:
        return "—"
    if info["maximum"] is not None:
        return f"{info['display_value']}/{info['maximum']} {info['unit']}"
    return f"{info['display_value']} {info['unit']}"


@register.filter
def work_type_label(work):
    if not work:
        return ""
    return WORK_TYPE_LABELS.get(work._meta.model_name, "")


@register.filter
def status_label_ru(user_work):
    if not user_work:
        return ""
    return STATUS_LABELS_RU.get(user_work.status, user_work.get_status_display())


@register.filter
def status_icon(user_work):
    if not user_work:
        return "bi bi-circle"
    return STATUS_ICONS.get(user_work.status, "bi bi-circle")


@register.filter
def feed_action_label(item):
    if not item:
        return ""
    return FEED_ACTION_LABELS_RU.get(item.action_type, item.get_action_type_display())


@register.filter
def feed_action_icon(item):
    if not item:
        return "bi bi-circle"
    return FEED_ACTION_ICONS.get(item.action_type, "bi bi-circle")
