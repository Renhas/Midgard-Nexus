from django.conf import settings


def modules(request):
    """Добавляет список модулей в контекст всех шаблонов."""
    return {
        "modules": settings.MODULES,
    }


def app_version(request):
    """Добавляет версию приложения в контекст всех шаблонов."""
    return {
        "app_version": settings.APP_VERSION,
    }
