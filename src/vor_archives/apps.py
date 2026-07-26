from django.apps import AppConfig


class VorArchivesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vor_archives'

    def ready(self):
        import vor_archives.signals  # noqa: F401
