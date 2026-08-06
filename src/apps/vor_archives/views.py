from django.conf import settings
from django.shortcuts import render

from .constants import AgeRatingChoices, UserWorkStatusChoices
from .models import Collection, Platform, BookGenre, FilmGenre, GameGenre

def _module_context():
    """Возвращает общие переменные шаблона для модуля vor_archives."""
    return next(m for m in settings.MODULES if m['url_name'] == 'vor_archives')


def index(request):
    """Главная страница модуля «Библиотека» — страница произведений."""
    module = _module_context()
    collections = Collection.objects.filter(user=request.user, parent=None)
    status_options = [{'value': v, 'label': l} for v, l in UserWorkStatusChoices.choices]
    age_rating_options = [{'value': v, 'label': l} for v, l in AgeRatingChoices.choices]
    platform_options = [{'value': p.id, 'label': p.name} for p in Platform.objects.all()] # type: ignore
    genre_models = [
        ('book', BookGenre, 'Книги'),
        ('film', FilmGenre, 'Фильмы'),
        ('game', GameGenre, 'Игры'),
    ]
    genres_nested = []
    for type_key, model, label in genre_models:
        options = [{'value': g.id, 'label': g.name} for g in model.objects.all()]
        if options:
            genres_nested.append({
                'title': label,
                'options': options,
                'name': f'genre_{type_key}',
                'show_condition': f"workTypes.includes('{type_key}')"
            })

    work_types_default = ['book', 'film', 'game']
    sort_fields = [
        {'value': 'custom', 'label': 'Свой порядок'},
        {'value': 'title', 'label': 'Название'},
        {'value': 'rating', 'label': 'Рейтинг'},
        {'value': 'status', 'label': 'Статус'},
        {'value': 'date_added', 'label': 'Дата добавления'},
    ]
    return render(request, 'vor_archives/artworks.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
        'active_section': 'artworks',
        'collections': collections,
        'status_options': status_options,
        'age_rating_options': age_rating_options,
        'platform_options': platform_options,
        'genres_nested': genres_nested,
        'sort_fields': sort_fields,
        'sort_field_default': 'custom',
        'sort_order_asc': True,
        'work_types': work_types_default,
    })


def dashboard(request):
    """Страница дашборда модуля «Библиотека»."""
    module = _module_context()
    return render(request, 'vor_archives/dashboard.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
        'active_section': 'dashboard',
    })


def attributes(request):
    """Страница атрибутов модуля «Библиотека»."""
    module = _module_context()
    return render(request, 'vor_archives/attributes.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
        'active_section': 'attributes',
    })
