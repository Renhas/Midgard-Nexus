"""Tests for apps.vor_archives.dashboard.services.stats."""

from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
import pytest

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import AgeRatingChoices, UserWorkStatusChoices
from apps.vor_archives.dashboard.services.stats import stats_payload
from apps.vor_archives.models import Book, UserWork
from apps.vor_archives.tests.factories import (
    BookFactory,
    FilmFactory,
    GameFactory,
    UserWorkFactory,
)


@pytest.mark.django_db
def test_stats_payload_opts_shape(user, book):
    UserWorkFactory(user=user, work=book)
    opts = stats_payload(user)["stats_opts"]

    for key in (
        "status_matrix",
        "age_matrix",
        "rating_matrix",
        "spent",
        "type_meta",
        "status_choices",
        "age_choices",
        "rating_choices",
    ):
        assert key in opts, f"stats_opts missing {key!r}"

    for type_key in ("book", "film", "game"):
        assert set(opts["status_matrix"][type_key]) == set(UserWorkStatusChoices.values)
        assert type_key in opts["spent"]
        assert opts["type_meta"][type_key]["label"]
        assert opts["type_meta"][type_key]["unit"]


@pytest.mark.django_db
def test_stats_payload_spent(user, book, movie, tv_show, game):
    tv_show.duration_minutes = 45
    tv_show.save()
    UserWorkFactory(user=user, work=book, progress=100)
    UserWorkFactory(user=user, work=movie, progress=120)
    UserWorkFactory(user=user, work=tv_show, progress=8)
    UserWorkFactory(user=user, work=game, progress=Decimal("5.5"))

    payload = stats_payload(user)
    spent = payload["stats_opts"]["spent"]

    assert spent["book"] == 100.0
    assert spent["film"] == 8.0
    assert spent["game"] == 5.5


@pytest.mark.django_db
def test_stats_payload_status_matrix(user, book, movie, tv_show, game):
    UserWorkFactory(user=user, work=book, status=UserWorkStatusChoices.DROPPED)
    UserWorkFactory(user=user, work=BookFactory(), status=UserWorkStatusChoices.DROPPED)
    UserWorkFactory(user=user, work=movie, status=UserWorkStatusChoices.IN_PROGRESS)
    UserWorkFactory(user=user, work=tv_show, status=UserWorkStatusChoices.PLANNING)
    UserWorkFactory(user=user, work=game, status=UserWorkStatusChoices.COMPLETED)

    payload = stats_payload(user)
    status_matrix = payload["stats_opts"]["status_matrix"]

    assert status_matrix["book"]["dropped"] == 2
    assert status_matrix["film"]["planning"] == 1
    assert status_matrix["film"]["in_progress"] == 1
    assert status_matrix["game"]["completed"] == 1
    assert sum(status_matrix["book"].values()) == 2
    assert sum(status_matrix["film"].values()) == 2
    assert sum(status_matrix["game"].values()) == 1


@pytest.mark.django_db
def test_stats_payload_age_matrix(user):
    UserWorkFactory(user=user, work=BookFactory(age_rating=AgeRatingChoices.RATING_0))
    UserWorkFactory(user=user, work=BookFactory(age_rating=AgeRatingChoices.RATING_0))
    UserWorkFactory(user=user, work=FilmFactory(age_rating=AgeRatingChoices.RATING_6))
    UserWorkFactory(
        user=user, work=FilmFactory(age_rating=AgeRatingChoices.RATING_12, tv=True)
    )
    UserWorkFactory(user=user, work=GameFactory(age_rating=AgeRatingChoices.RATING_16))
    UserWorkFactory(user=user, work=GameFactory(age_rating=AgeRatingChoices.RATING_18))
    UserWorkFactory(user=user, work=FilmFactory())

    payload = stats_payload(user)
    age_matrix = payload["stats_opts"]["age_matrix"]

    assert age_matrix["book"]["0+"] == 2
    assert age_matrix["film"]["6+"] == 1
    assert age_matrix["film"]["12+"] == 1
    assert age_matrix["film"][""] == 1
    assert age_matrix["game"]["16+"] == 1
    assert age_matrix["game"]["18+"] == 1
    assert sum(age_matrix["book"].values()) == 2
    assert sum(age_matrix["film"].values()) == 3
    assert sum(age_matrix["game"].values()) == 2


@pytest.mark.django_db
def test_stats_payload_rating_matrix(user, book, movie, tv_show, game):
    UserWorkFactory(user=user, work=book, rating=8)
    UserWorkFactory(user=user, work=BookFactory(), rating=8)
    UserWorkFactory(user=user, work=movie, rating=7)
    UserWorkFactory(user=user, work=tv_show, rating=2)
    UserWorkFactory(user=user, work=game)

    payload = stats_payload(user)
    rating_matrix = payload["stats_opts"]["rating_matrix"]

    assert rating_matrix["book"]["8"] == 2
    assert rating_matrix["film"]["7"] == 1
    assert rating_matrix["film"]["2"] == 1
    assert rating_matrix["game"][""] == 1
    assert sum(rating_matrix["book"].values()) == 2
    assert sum(rating_matrix["film"].values()) == 2
    assert sum(rating_matrix["game"].values()) == 1


@pytest.mark.django_db
def test_stats_payload_exclude_other_user(user, book):
    UserWorkFactory(user=user, work=book, rating=8)
    other = UserFactory()
    UserWorkFactory(user=other, work=BookFactory(), rating=10)

    payload = stats_payload(user)
    rating_matrix = payload["stats_opts"]["rating_matrix"]

    assert rating_matrix["book"]["8"] == 1
    assert sum(rating_matrix["book"].values()) == 1


@pytest.mark.django_db
def test_stats_payload_empty_library(user):
    empty_opts = stats_payload(user)["stats_opts"]
    assert empty_opts["spent"] == {"book": 0.0, "film": 0.0, "game": 0.0}
    for type_key in ("book", "film", "game"):
        assert sum(empty_opts["status_matrix"][type_key].values()) == 0
        assert sum(empty_opts["age_matrix"][type_key].values()) == 0
        assert sum(empty_opts["rating_matrix"][type_key].values()) == 0
