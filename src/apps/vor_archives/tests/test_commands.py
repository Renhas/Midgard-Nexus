import pytest
from django.core.management import call_command

from apps.vor_archives.models import UserWork


@pytest.mark.django_db
def test_seed_demo_creates_unique_positions(admin_user):
    call_command("seed_demo", "--clear")

    positions = list(
        UserWork.objects.order_by("order_position").values_list(
            "order_position", flat=True
        )
    )
    assert positions == list(range(len(positions)))
