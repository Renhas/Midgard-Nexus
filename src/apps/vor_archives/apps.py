from django.apps import AppConfig


class VorArchivesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vor_archives"

    def ready(self):
        import apps.vor_archives.signals  # noqa: F401
