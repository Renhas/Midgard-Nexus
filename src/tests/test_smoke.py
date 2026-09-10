"""Smoke test: test settings, isolated PostgreSQL, live connection."""

import os

import pytest
from django.conf import settings
from django.db import connection


@pytest.mark.django_db
def test_postgres_test_settings_and_connection():
    assert settings.SETTINGS_MODULE == "config.settings.test"
    assert connection.vendor == "postgresql"

    db_name = connection.settings_dict["NAME"]
    assert db_name.startswith("test_")
    assert db_name != os.getenv("DB_NAME")

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
