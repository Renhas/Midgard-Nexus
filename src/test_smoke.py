"""Minimal smoke test so pytest has a green run until app tests appear."""


def test_django_settings_load():
    from django.conf import settings

    assert settings.SECRET_KEY
    assert settings.configured
