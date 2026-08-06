from django import template

register = template.Library()


@register.filter
def get_work_type_icon(user_work):
    if not user_work or not hasattr(user_work, 'work'):
        return ''
    work = user_work.work
    model_name = work._meta.model_name
    icons = {
        'book': 'icon-book-text',
        'film': 'icon-clapperboard',
        'series': 'icon-film',
        'game': 'icon-gamepad-2',
    }
    return icons.get(model_name, 'bi bi-collection')


@register.filter
def format_progress(user_work):
    if not user_work or not hasattr(user_work, 'work'):
        return '—'
    work = user_work.work
    model_name = work._meta.model_name
    progress = user_work.progress or 0

    if model_name == 'book':
        max_pages = getattr(work, 'pages', 0)
        return f'{progress}/{max_pages} стр.'
    elif model_name == 'film':
        duration = getattr(work, 'duration_minutes', 0)
        return f'{progress}/{duration} мин.'
    elif model_name == 'game':
        return f'{progress} ч.'
    return '—'
