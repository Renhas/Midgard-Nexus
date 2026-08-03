from django.conf import settings


def modules(request):
    """Добавляет список модулей в контекст всех шаблонов."""
    return {
        'modules': settings.MODULES,
    }
