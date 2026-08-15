from django import template

from ..constants import FilmTypeChoices

register = template.Library()


WORK_TYPE_ICONS = {
    'book': 'icon-book-text',
    'film': 'icon-clapperboard',
    'game': 'icon-gamepad-2',
}


@register.filter
def get_model_icon(obj):
    if not obj:
        return 'bi bi-collection'
    return WORK_TYPE_ICONS.get(obj._meta.model_name, 'bi bi-collection')


@register.filter
def get_work_type_icon(user_work):
    if not user_work or not hasattr(user_work, 'work'):
        return ''
    return get_model_icon(user_work.work)


@register.filter
def format_progress(user_work):
    if not user_work or not hasattr(user_work, 'work'):
        return '—'
    work = user_work.work
    model_name = work._meta.model_name
    progress = round(user_work.progress) or 0

    if model_name == 'book':
        max_pages = work.pages
        return f'{progress}/{max_pages} стр.'
    elif model_name == 'game':
        return f'{progress} ч.'
    elif model_name == 'film':
        f_type = work.film_type
        if f_type == FilmTypeChoices.MOVIE:
            duration = work.duration_minutes
            return f'{progress}/{duration} мин.'
        if f_type == FilmTypeChoices.TV_SHOW:
            return f"{progress}/{work.episode_count} эп."
    return '—'
