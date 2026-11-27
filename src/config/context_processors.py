from django.conf import settings
from django.templatetags.static import static
from django.contrib.messages import get_messages

from config.importmap import IMPORTMAP_PATHS


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


def importmap(request):
    """Expose module specifier -> URL for the import map in base.html.

    Uses Django's static() so that in production with
    ManifestStaticFilesStorage the URLs are content-hashed, which is
    what makes <script type="importmap"> survive nginx's
    `Cache-Control: public, immutable`.
    """
    return {
        "importmap_items": {
            specifier: static(path) for specifier, path in IMPORTMAP_PATHS.items()
        }
    }


def toast_config(request):
    """Глобальные настройки уведомлений (задел под настройки профиля)."""
    return {
        "toast_config": {
            "maxVisible": 5,
            "duration": 4000,
            "errorDuration": 7000,
        }
    }


def django_messages(request):
    """Передаёт сообщения django.contrib.messages в шаблон для вывода через тосты."""
    storage = get_messages(request)
    return {
        "django_messages": [
            {
                "level": msg.level_tag or "info",
                "message": str(msg.message),
            }
            for msg in storage
        ]
    }
