import pytest
from django.core.management import call_command

from apps.vor_archives.models import UserWork


@pytest.mark.django_db
def test_seed_demo_creates_unique_positions(admin_user):
    call_command("seed_demo", "--clear")

    positions = list(UserWork.objects.values_list("order_position", flat=True))
    assert len(positions) == len(set(positions))
    assert positions == sorted(positions)
