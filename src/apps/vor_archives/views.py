from django.conf import settings
from django.shortcuts import render


def _module_context():
    """Возвращает общие переменные шаблона для модуля vor_archives."""
    return next(m for m in settings.MODULES if m['url_name'] == 'vor_archives')


def index(request):
    """Главная страница модуля «Библиотека» — страница произведений."""
    from .models import Collection
    module = _module_context()
    collections = Collection.objects.filter(user=request.user, parent=None)
    return render(request, 'vor_archives/artworks.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
        'active_section': 'artworks',
        'collections': collections,
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
