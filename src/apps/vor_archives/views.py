from django.conf import settings
from django.shortcuts import render


def index(request):
    """Заглушка модуля «Библиотека»."""
    module = next(m for m in settings.MODULES if m['url_name'] == 'vor_archives')
    return render(request, 'vor_archives/wip.html', {
        'module_name': module['name'],
        'module_icon': module['icon'],
        'module_color': module['color'],
    })
