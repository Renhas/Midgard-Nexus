"""Tests for apps.vor_archives dashboard aggregations."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from django.urls import reverse

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import UserWorkStatusChoices, AgeRatingChoices
from apps.vor_archives.templatetags.vor_archives_extras import (
    FEED_ACTION_ICONS,
    FEED_ACTION_LABELS_RU,
)
from apps.vor_archives.dashboard import (
    attrs_payload,
    feed_page,
    heatmap_payload,
    heatmap_range,
    parse_heatmap_year,
    progress_spent,
    stats_payload,
    _monday,
    _sunday,
    _heat_level,
)
from apps.vor_archives.models import FeedItem
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    FilmFactory,
    FilmGenreFactory,
    GameFactory,
    GameGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
)

# ─── Dashboard ──────────────────────────────────────────────────────────


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
    UserWorkFactory(user=user, work=game, progress=Decimal("5.5"))  # для дробного числа

    payload = stats_payload(user)
    spent = payload["stats_opts"]["spent"]

    assert spent["book"] == 100.0  # страницы
    assert spent["film"] == 8.0  # 120 / 60 (Movie) + 8 * 45 / 60 (TV_Show)
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
def test_attrs_payload_genre_name_collision(user, book, movie, game):
    shared = "Fantasy"
    unique = "Action"
    book.genres.add(BookGenreFactory(name=shared))
    movie.genres.add(FilmGenreFactory(name=shared))
    game.genres.add(GameGenreFactory(name=unique))
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    genre_names = {item["name"] for item in attrs["genres"]}

    assert "Fantasy (Книги)" in genre_names
    assert "Fantasy (Фильмы)" in genre_names
    assert "Action (Игры)" in genre_names


@pytest.mark.django_db
def test_attrs_payload_tags_counts_and_sorting(user, book, game):
    tags = {name: TagFactory(name=name) for name in ["alpha", "beta", "gamma"]}
    book.tags.add(*tags.values())
    game.tags.add(tags["beta"])
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    tag_counts = {item["name"]: item["count"] for item in attrs["tags"]}

    assert tag_counts == {"alpha": 1, "beta": 2, "gamma": 1}
    assert [item["name"] for item in attrs["tags"]] == [
        "beta",
        "alpha",
        "gamma",
    ]


@pytest.mark.django_db
def test_attrs_payload_persons_counts_and_sorting(user, book, game):
    authors = {
        name: PersonFactory(name=name) for name in ["Author A", "Author B", "Author C"]
    }
    book.authors.add(*authors.values())
    game.authors.add(authors["Author B"])
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    person_counts = {item["name"]: item["count"] for item in attrs["persons"]}

    assert person_counts == {"Author A": 1, "Author B": 2, "Author C": 1}
    assert [item["name"] for item in attrs["persons"]] == [
        "Author B",
        "Author A",
        "Author C",
    ]


@pytest.mark.django_db
def test_attrs_payload_platform_counts_and_sorting(user):
    platforms = {name: PlatformFactory(name=name) for name in ["PC", "Xbox", "Switch"]}
    first_game = GameFactory()
    second_game = GameFactory()
    first_game.platforms.add(*platforms.values())
    second_game.platforms.add(platforms["Xbox"])
    UserWorkFactory(user=user, work=first_game)
    UserWorkFactory(user=user, work=second_game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    platforms_counts = {item["name"]: item["count"] for item in attrs["platforms"]}

    assert platforms_counts == {"PC": 1, "Xbox": 2, "Switch": 1}
    assert [item["name"] for item in attrs["platforms"]] == ["Xbox", "PC", "Switch"]


@pytest.mark.django_db
def test_attrs_payload_genres_counts_and_sorting(user):
    genres = {
        name: GameGenreFactory(name=name) for name in ["Action", "RPG", "Adventure"]
    }
    first_game = GameFactory()
    second_game = GameFactory()
    first_game.genres.add(*genres.values())
    second_game.genres.add(genres["RPG"])
    UserWorkFactory(user=user, work=first_game)
    UserWorkFactory(user=user, work=second_game)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]
    genres_counts = {item["name"]: item["count"] for item in attrs["genres"]}

    assert genres_counts == {"Action (Игры)": 1, "RPG (Игры)": 2, "Adventure (Игры)": 1}
    assert [item["name"] for item in attrs["genres"]] == [
        "RPG (Игры)",
        "Action (Игры)",
        "Adventure (Игры)",
    ]


@pytest.mark.django_db
def test_attrs_payload_excludes_orphans_and_foreign(user, game):
    TagFactory(name="orphan-tag")
    PersonFactory(name="orphan-author")
    PlatformFactory(name="orphan-platform")
    GameGenreFactory(name="orphan-genre")

    game.tags.add(TagFactory(name="alpha"))
    game.authors.add(PersonFactory(name="Author A"))
    game.platforms.add(PlatformFactory(name="PC"))
    game.genres.add(GameGenreFactory(name="RPG"))

    UserWorkFactory(user=user, work=game)

    other = UserFactory()
    other_book = BookFactory()
    other_book.tags.add(TagFactory(name="foreign-tag"))
    UserWorkFactory(user=other, work=other_book)

    payload = attrs_payload(user)
    attrs = payload["attrs_opts"]["attrs"]

    tag_names = {item["name"] for item in attrs["tags"]}
    person_names = {item["name"] for item in attrs["persons"]}
    platform_names = {item["name"] for item in attrs["platforms"]}
    genre_names = {item["name"] for item in attrs["genres"]}

    # Positive control
    assert "alpha" in tag_names
    assert "Author A" in person_names
    assert "PC" in platform_names
    assert "RPG (Игры)" in genre_names
    # Orphans
    assert "orphan-tag" not in tag_names
    assert "orphan-author" not in person_names
    assert "orphan-platform" not in platform_names
    assert not any(name.startswith("orphan-genre") for name in genre_names)
    # Foreign
    assert "foreign-tag" not in tag_names


@pytest.mark.django_db
def test_feed_page_orders_and_paginates(user, book, movie):
    # Сигнал создаёт FeedItem(action_type="added") при создании UserWork.
    # Если поведение сигнала изменится, тест нужно будет адаптировать.
    first = UserWorkFactory(user=user, work=book)
    second = UserWorkFactory(user=user, work=movie)
    older = FeedItem.objects.filter(user_work=first, action_type="added").get()
    newer = FeedItem.objects.filter(user_work=second, action_type="added").get()
    _set_timestamp(older, timezone.now() - timedelta(hours=2))
    _set_timestamp(newer, timezone.now() - timedelta(hours=1))

    page, has_more = feed_page(user, offset=0, limit=1)

    assert has_more is True
    assert page[0]["work_title"] == movie.title
    assert page[0]["detail_url"] == reverse(
        "vor_archives:artworks:detail", args=[second.pk]
    )
    assert page[0]["label"] == FEED_ACTION_LABELS_RU["added"]
    assert page[0]["icon"] == FEED_ACTION_ICONS["added"]

    rest, rest_more = feed_page(user, offset=1, limit=1)
    assert rest[0]["work_title"] == book.title
    assert rest[0]["detail_url"] == reverse(
        "vor_archives:artworks:detail", args=[first.pk]
    )
    assert rest_more is False


@pytest.mark.django_db
def test_feed_page_tie_breaks_by_pk_desc(user, book, movie):
    first = UserWorkFactory(user=user, work=book)
    second = UserWorkFactory(user=user, work=movie)
    item_a = FeedItem.objects.filter(user_work=first, action_type="added").get()
    item_b = FeedItem.objects.filter(user_work=second, action_type="added").get()

    same_time = timezone.now() - timedelta(hours=1)
    _set_timestamp(item_a, same_time)
    _set_timestamp(item_b, same_time)

    page, _ = feed_page(user, limit=2)

    assert page[0]["id"] == item_b.pk
    assert page[1]["id"] == item_a.pk


@pytest.mark.django_db
def test_feed_page_filters_by_user(user, book):
    UserWorkFactory(user=user, work=book)
    other = UserFactory()
    other_book = BookFactory()
    UserWorkFactory(user=other, work=other_book)

    page, has_more = feed_page(user)

    assert len(page) == 1
    assert page[0]["work_title"] == book.title
    assert has_more is False


@pytest.mark.django_db
def test_feed_page_empty(user):
    page, has_more = feed_page(user)

    assert page == []
    assert has_more is False


@pytest.mark.django_db
def test_feed_item_payload_with_deleted_user_work(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    user_work.delete()  # FeedItem.user_work → NULL

    page, _ = feed_page(user)

    assert len(page) == 1
    assert page[0]["work_title"] == ""
    assert page[0]["detail_url"] == ""


@pytest.mark.django_db
def test_heatmap_payload_grid_structure(user):
    """7 дней в неделе, month_labels совпадает по длине с weeks."""
    payload = heatmap_payload(user, year=2024)

    assert payload["weekday_labels"] == ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    assert all(len(week) == 7 for week in payload["weeks"])
    assert len(payload["month_labels"]) == len(payload["weeks"])


@pytest.mark.django_db
def test_heatmap_counts_days_in_selected_year(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.filter(user_work=user_work).get()
    when = timezone.make_aware(datetime(2024, 3, 15, 12, 0))
    _set_timestamp(item, when)

    payload = heatmap_payload(user, year=2024)
    counted = [day for week in payload["weeks"] for day in week if day["count"]]

    assert payload["year"] == 2024
    assert len(counted) == 1
    assert counted[0]["date"] == "2024-03-15"
    assert counted[0]["count"] == 1


@pytest.mark.django_db
def test_heatmap_payload_default_range_is_last_year(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.get(user_work=user_work)
    _set_timestamp(item, timezone.make_aware(datetime(2024, 3, 15, 12, 0)))

    payload = heatmap_payload(user, today=date(2024, 6, 1))

    assert payload["year"] is None
    counted = [day for week in payload["weeks"] for day in week if day["count"]]
    assert counted[0]["date"] == "2024-03-15"


@pytest.mark.django_db
def test_heatmap_payload_excludes_other_years(user, book):
    user_work = UserWorkFactory(user=user, work=book)
    item = FeedItem.objects.get(user_work=user_work)
    _set_timestamp(item, timezone.make_aware(datetime(2023, 3, 15, 12, 0)))

    payload = heatmap_payload(user, year=2024)
    counted = [day for week in payload["weeks"] for day in week if day["count"]]

    assert counted == []
    assert payload["max_count"] == 0


@pytest.mark.django_db
def test_heatmap_payload_years_deduped_and_sorted(user):
    for _ in range(2):
        uw = UserWorkFactory(user=user, work=BookFactory())
        item = FeedItem.objects.get(user_work=uw, action_type="added")
        _set_timestamp(item, timezone.make_aware(datetime(2020, 5, 1, 12, 0)))

    for _ in range(2):
        UserWorkFactory(user=user, work=BookFactory())

    payload = heatmap_payload(user)

    assert payload["years"] == [2020, timezone.localdate().year]


@pytest.mark.django_db
def test_heatmap_payload_is_user_scoped(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    payload = heatmap_payload(user)

    assert payload["max_count"] == 0
    counted = [day for week in payload["weeks"] for day in week if day["count"]]
    assert counted == []


def test_heatmap_range_for_year():
    start, end, grid_start, grid_end = heatmap_range(2025)

    assert start == date(2025, 1, 1)
    assert end == date(2025, 12, 31)
    # 2025-01-01 — среда, поэтому сетка начинается с понедельника 2024-12-30
    assert grid_start == date(2024, 12, 30)
    # 2025-12-31 — среда, поэтому сетка заканчивается воскресеньем 2026-01-04
    assert grid_end == date(2026, 1, 4)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", None),
        (None, None),
        ("nope", None),
        ("1800", None),
        ("2101", None),
        ("2024.0", None),
        ("1970", 1970),
        ("2026", 2026),
        ("2100", 2100),
        (" 2026 ", 2026),
    ],
)
def test_parse_heatmap_year(raw, expected):
    assert parse_heatmap_year(raw) == expected


@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2025, 1, 6), date(2025, 1, 6)),  # понедельник → тот же день
        (date(2025, 1, 7), date(2025, 1, 6)),  # вторник → назад на 1
        (date(2025, 1, 12), date(2025, 1, 6)),  # воскресенье → назад на 6
    ],
)
def test_monday(day, expected):
    assert _monday(day) == expected


@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2025, 1, 12), date(2025, 1, 12)),  # воскресенье → тот же день
        (date(2025, 1, 11), date(2025, 1, 12)),  # суббота → вперёд на 1
        (date(2025, 1, 6), date(2025, 1, 12)),  # понедельник → вперёд на 6
    ],
)
def test_sunday(day, expected):
    assert _sunday(day) == expected


@pytest.mark.parametrize(
    "count, max_count, expected",
    [
        # Нет активности
        (0, 0, 0),
        (0, 12, 0),
        (-1, 10, 0),  # защита от отрицательных
        # Спецслучай: только одна работа или ноль — считаем максимумом
        (1, 1, 4),
        (5, 1, 4),  # count > max_count, но max<=1 → 4
        (1, 0, 4),  # max_count=0 при count>0
        # Границы отношений (max=12 для чистых дробей)
        (3, 12, 1),  # ровно 0.25 → level 1 (условие <=)
        (4, 12, 2),  # 0.333 → level 2
        (6, 12, 2),  # ровно 0.5 → level 2
        (7, 12, 3),  # 0.583 → level 3
        (9, 12, 3),  # ровно 0.75 → level 3
        (10, 12, 4),  # 0.833 → level 4
        (12, 12, 4),  # 1.0 → level 4
    ],
)
def test_heat_level(count, max_count, expected):
    assert _heat_level(count, max_count) == expected
