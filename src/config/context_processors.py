from django.conf import settings
from django.templatetags.static import static

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
