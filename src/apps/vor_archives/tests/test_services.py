"""Tests for apps.vor_archives dashboard aggregations."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import UserWorkStatusChoices
from apps.vor_archives.dashboard import (
    charts_payload,
    feed_page,
    heatmap_payload,
    heatmap_range,
    parse_heatmap_year,
    progress_spent,
    stats_payload,
)
from apps.vor_archives.models import FeedItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmFactory,
    FilmGenreFactory,
    GameFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
)


def _set_timestamp(item, when):
    FeedItem.objects.filter(pk=item.pk).update(timestamp=when)
    item.refresh_from_db()
    return item


@pytest.mark.django_db
def test_tv_show_hours_uses_episode_duration_times_progress(user, tv_show):
    tv_show.duration_minutes = 45
    tv_show.save()
    user_work = UserWorkFactory(user=user, work=tv_show, progress=Decimal("4"))

    type_key, amount, unit = progress_spent(user_work)

    assert type_key == "film"
    assert unit == "ч."
    assert amount == 3.0


@pytest.mark.django_db
def test_movie_hours_use_progress_minutes(user, movie):
    movie.duration_minutes = 90
    movie.save()
    user_work = UserWorkFactory(user=user, work=movie, progress=Decimal("90"))

    _, amount, unit = progress_spent(user_work)

    assert unit == "ч."
    assert amount == 1.5


@pytest.mark.django_db
def test_book_and_game_progress_passthrough(user, book, game):
    book_uw = UserWorkFactory(user=user, work=book, progress=Decimal("150"))
    game_uw = UserWorkFactory(user=user, work=game, progress=Decimal("12.5"))

    assert progress_spent(book_uw) == ("book", 150.0, "стр.")
    assert progress_spent(game_uw) == ("game", 12.5, "ч.")


@pytest.mark.django_db
def test_stats_payload_counts_percents_and_hidden_works(user, book, movie, game):
    UserWorkFactory(
        user=user,
        work=book,
        status=UserWorkStatusChoices.PLANNING,
        rating=8,
        progress=100,
        is_hidden=True,
    )
    movie_uw = UserWorkFactory(
        user=user,
        work=movie,
        status=UserWorkStatusChoices.IN_PROGRESS,
        rating=6,
        progress=120,
    )
    movie_uw.status = UserWorkStatusChoices.COMPLETED
    movie_uw.save()
    UserWorkFactory(
        user=user,
        work=game,
        status=UserWorkStatusChoices.PLANNING,
        progress=Decimal("5"),
    )
    other = UserFactory()
    UserWorkFactory(user=other, work=BookFactory(), rating=10)

    payload = stats_payload(user)
    by_key = {card["key"]: card for card in payload["type_cards"]}

    assert payload["total"] == 3
    assert by_key["book"]["count"] == 1
    assert by_key["book"]["percent"] == "33.3%"
    assert payload["status_matrix"]["planning"]["book"] == 1
    assert payload["status_matrix"]["planning"]["game"] == 1
    assert payload["status_matrix"]["completed"]["film"] == 1
    progress = {card["key"]: card for card in payload["progress_cards"]}
    assert progress["book"]["avg_rating"] == 8.0
    assert progress["film"]["spent"] == 2.0
    assert progress["game"]["spent"] == 5.0
    assert progress["game"]["avg_rating_display"] == "—"


@pytest.mark.django_db
def test_charts_payload_pie_and_genre_name_collision(user):
    shared = "Fantasy"
    book = BookFactory(age_rating="12+")
    film = FilmFactory(age_rating="")
    book.genres.add(BookGenreFactory(name=shared))
    film.genres.add(FilmGenreFactory(name=shared))
    book.tags.add(TagFactory(name="space"))
    book.authors.add(PersonFactory(name="Author A"))
    game = GameFactory()
    game.platforms.add(PlatformFactory(name="PC"))
    book_uw = UserWorkFactory(
        user=user, work=book, rating=9, status=UserWorkStatusChoices.IN_PROGRESS
    )
    book_uw.status = UserWorkStatusChoices.COMPLETED
    book_uw.save()
    UserWorkFactory(user=user, work=film, rating=None)
    UserWorkFactory(user=user, work=game, rating=7)

    payload = charts_payload(user)
    status_keys = {item["key"] for item in payload["pies"]["status"]}
    rating_keys = {item["key"] for item in payload["pies"]["rating"]}
    age_keys = {item["key"] for item in payload["pies"]["age_rating"]}
    genre_names = {item["name"] for item in payload["attrs"]["genres"]}

    assert "completed" in status_keys
    assert "9" in rating_keys
    assert "" in rating_keys
    assert "12+" in age_keys
    assert "" in age_keys
    assert "Fantasy (Книги)" in genre_names
    assert "Fantasy (Фильмы)" in genre_names
    assert payload["attrs"]["tags"][0]["name"] == "space"
    assert payload["attrs"]["platforms"][0]["name"] == "PC"


@pytest.mark.django_db
def test_feed_page_orders_and_paginates(user, book, movie):
    first = UserWorkFactory(user=user, work=book)
    second = UserWorkFactory(user=user, work=movie)
    older = FeedItem.objects.filter(user_work=first, action_type="added").get()
    newer = FeedItem.objects.filter(user_work=second, action_type="added").get()
    _set_timestamp(older, timezone.now() - timedelta(hours=2))
    _set_timestamp(newer, timezone.now() - timedelta(hours=1))

    page, has_more = feed_page(user, offset=0, limit=1)

    assert has_more is True
    assert page[0]["work_title"] == movie.title
    assert page[0]["detail_url"]
    rest, rest_more = feed_page(user, offset=1, limit=1)
    assert rest[0]["work_title"] == book.title
    assert rest_more is False


@pytest.mark.django_db
def test_heatmap_counts_days_in_selected_year(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.filter(user_work=user_work).first()
    when = timezone.make_aware(datetime(2024, 3, 15, 12, 0))
    _set_timestamp(item, when)

    payload = heatmap_payload(user, year=2024, today=date(2024, 12, 31))
    counted = [day for week in payload["weeks"] for day in week if day["count"]]

    assert payload["year"] == 2024
    assert counted[0]["date"] == "2024-03-15"
    assert counted[0]["count"] == 1
    start, end, *_ = heatmap_range(2024, today=date(2024, 12, 31))
    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)


def test_parse_heatmap_year():
    assert parse_heatmap_year("") is None
    assert parse_heatmap_year("2024") == 2024
    assert parse_heatmap_year("nope") is None
    assert parse_heatmap_year("1800") is None
