from django.conf import settings
from django.shortcuts import render


def _module_context():
    """Возвращает общие переменные шаблона для модуля vor_archives."""
    return next(m for m in settings.MODULES if m['url_name'] == 'vor_archives')


def index(request):
    """Главная страница модуля «Библиотека» — страница коллекции."""
    module = _module_context()
    return render(request, 'vor_archives/collection.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
        'active_section': 'collection',
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
