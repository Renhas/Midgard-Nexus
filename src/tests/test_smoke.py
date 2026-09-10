"""Smoke test: PostgreSQL is reachable and Django migrations apply."""

import pytest
from django.core.management import call_command
from django.db import connection


@pytest.mark.django_db
def test_postgres_migrations_apply():
    assert connection.vendor == "postgresql"

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1

    call_command("migrate", verbosity=0, interactive=False)
    call_command("migrate", check=True, verbosity=0)

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM django_migrations")
        assert cursor.fetchone()[0] > 0
