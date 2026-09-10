"""Tests for apps.vor_archives models."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import FilmTypeChoices, WorkRelationTypeChoices
from apps.vor_archives.models import Film, UserWork, WorkRelation
from apps.vor_archives.tests.factories import (
    BookFactory,
    BookGenreFactory,
    CollectionFactory,
    CollectionItemFactory,
    FilmFactory,
    FilmGenreFactory,
    GameFactory,
    GameGenreFactory,
    PersonFactory,
    PlatformFactory,
    TagFactory,
    UserWorkFactory,
    WorkRelationFactory,
)

LOOKUP_FACTORIES = (
    PersonFactory,
    PlatformFactory,
    TagFactory,
    BookGenreFactory,
    FilmGenreFactory,
    GameGenreFactory,
)


def _ct(obj):
    return ContentType.objects.get_for_model(obj)


# ─── Film ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_film_movie_without_episodes_saves(movie):
    movie.refresh_from_db()
    assert movie.film_type == FilmTypeChoices.MOVIE
    assert movie.episode_count is None


@pytest.mark.django_db
def test_film_tv_show_with_min_and_typical_episode_count_saves():
    FilmFactory(tv=True, episode_count=1)
    FilmFactory(tv=True, episode_count=10)


@pytest.mark.django_db
@pytest.mark.parametrize("episode_count", [1, 5])
def test_film_movie_with_episode_count_raises(episode_count):
    film = Film(
        title="Movie",
        duration_minutes=90,
        film_type=FilmTypeChoices.MOVIE,
        episode_count=episode_count,
    )
    with pytest.raises(ValidationError) as exc_info:
        film.save()
    assert "episode_count" in exc_info.value.message_dict


@pytest.mark.django_db
def test_film_tv_show_without_episode_count_raises():
    film = Film(
        title="Show",
        duration_minutes=40,
        film_type=FilmTypeChoices.TV_SHOW,
        episode_count=None,
    )
    with pytest.raises(ValidationError) as exc_info:
        film.save()
    assert "episode_count" in exc_info.value.message_dict


@pytest.mark.django_db
def test_film_tv_show_zero_episodes_fails_field_validation():
    film = Film(
        title="Show",
        duration_minutes=40,
        film_type=FilmTypeChoices.TV_SHOW,
        episode_count=0,
    )
    with pytest.raises(ValidationError):
        film.save()


@pytest.mark.django_db(transaction=True)
def test_film_db_allows_valid_episode_rules():
    Film.objects.bulk_create(
        [
            Film(
                title="Movie",
                duration_minutes=90,
                film_type=FilmTypeChoices.MOVIE,
                episode_count=None,
            ),
            Film(
                title="Show",
                duration_minutes=40,
                film_type=FilmTypeChoices.TV_SHOW,
                episode_count=1,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
def test_film_db_rejects_movie_with_episode_count():
    with pytest.raises(IntegrityError):
        Film.objects.bulk_create(
            [
                Film(
                    title="Movie",
                    duration_minutes=90,
                    film_type=FilmTypeChoices.MOVIE,
                    episode_count=1,
                )
            ]
        )


@pytest.mark.django_db(transaction=True)
def test_film_db_rejects_tv_show_without_episode_count():
    with pytest.raises(IntegrityError):
        Film.objects.bulk_create(
            [
                Film(
                    title="Show",
                    duration_minutes=40,
                    film_type=FilmTypeChoices.TV_SHOW,
                    episode_count=None,
                )
            ]
        )


# ─── WorkRelation ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_work_relation_valid_pairs_save(book, movie):
    WorkRelationFactory(
        source=book,
        target=BookFactory(),
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )
    WorkRelationFactory(
        source=book,
        target=movie,
        relation_type=WorkRelationTypeChoices.ADAPTATION,
    )
    WorkRelationFactory(
        source=book,
        target=FilmFactory(),
        relation_type=WorkRelationTypeChoices.OTHER,
    )


@pytest.mark.django_db
def test_work_relation_invalid_types_raise(book, movie):
    with pytest.raises(ValidationError):
        WorkRelationFactory(
            source=book,
            target=BookFactory(),
            relation_type=WorkRelationTypeChoices.ADAPTATION,
        )
    with pytest.raises(ValidationError):
        WorkRelationFactory(
            source=book,
            target=movie,
            relation_type=WorkRelationTypeChoices.SEQUEL,
        )


@pytest.mark.django_db
def test_work_relation_rejects_missing_source_or_target(book):
    ct = _ct(book)
    missing = WorkRelation(
        source_content_type=ct,
        source_object_id=999_999,
        target_content_type=ct,
        target_object_id=book.pk,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )
    with pytest.raises(ValidationError):
        missing.save()

    missing_target = WorkRelation(
        source_content_type=ct,
        source_object_id=book.pk,
        target_content_type=ct,
        target_object_id=999_999,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )
    with pytest.raises(ValidationError):
        missing_target.save()


@pytest.mark.django_db
def test_work_relation_reverse_pair_raises(book):
    other = BookFactory()
    WorkRelationFactory(source=book, target=other)
    with pytest.raises(ValidationError, match="уже есть связь"):
        WorkRelationFactory(source=other, target=book)


@pytest.mark.django_db(transaction=True)
def test_work_relation_same_direction_duplicate_hits_unique(book):
    other = BookFactory()
    WorkRelationFactory(source=book, target=other)
    duplicate = WorkRelation(
        source_content_type=_ct(book),
        source_object_id=book.pk,
        target_content_type=_ct(other),
        target_object_id=other.pk,
        relation_type=WorkRelationTypeChoices.REMAKE,
    )
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            duplicate.save()


@pytest.mark.django_db
def test_work_relation_shared_source_or_target_allowed(book):
    WorkRelationFactory(source=book, target=BookFactory())
    WorkRelationFactory(source=book, target=BookFactory())
    shared_target = BookFactory()
    WorkRelationFactory(source=BookFactory(), target=shared_target)
    WorkRelationFactory(source=BookFactory(), target=shared_target)


@pytest.mark.django_db
def test_work_relation_self_loop_raises(book):
    with pytest.raises(ValidationError, match="Цикличн"):
        WorkRelationFactory(source=book, target=book)


@pytest.mark.django_db
def test_work_relation_sequel_chain_cycle_raises():
    a, b, c = BookFactory(), BookFactory(), BookFactory()
    WorkRelationFactory(source=a, target=b)
    WorkRelationFactory(source=b, target=c)
    with pytest.raises(ValidationError, match="Цикличн"):
        WorkRelationFactory(source=c, target=a)


@pytest.mark.django_db
def test_work_relation_other_incoming_creates_cycle():
    a, b, c = BookFactory(), BookFactory(), BookFactory()
    WorkRelationFactory(source=a, target=b, relation_type=WorkRelationTypeChoices.OTHER)
    WorkRelationFactory(source=c, target=b)
    with pytest.raises(ValidationError, match="Цикличн"):
        WorkRelationFactory(source=a, target=c)


@pytest.mark.django_db
def test_work_relation_separate_chains_can_be_joined():
    a, b, c, d = BookFactory(), BookFactory(), BookFactory(), BookFactory()
    WorkRelationFactory(source=a, target=b)
    WorkRelationFactory(source=c, target=d)
    WorkRelationFactory(source=b, target=c)


# ─── UserWork ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [None, 1, 10])
def test_user_work_rating_bounds_save(book, user, rating):
    UserWorkFactory(user=user, work=book, rating=rating)


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [0, 11])
def test_user_work_rating_outside_bounds_raises(book, user, rating):
    with pytest.raises(ValidationError):
        UserWorkFactory(user=user, work=book, rating=rating)


@pytest.mark.django_db
@pytest.mark.parametrize("work_factory", [BookFactory, FilmFactory, GameFactory])
def test_user_work_accepts_each_work_type(user, work_factory):
    UserWorkFactory(user=user, work=work_factory())


@pytest.mark.django_db
def test_user_work_rejects_missing_work(user, book):
    uw = UserWork(
        user=user,
        work_content_type=_ct(book),
        work_object_id=999_999,
    )
    with pytest.raises(ValidationError):
        uw.save()


@pytest.mark.django_db(transaction=True)
def test_user_work_unique_per_user_and_work(book, user):
    UserWorkFactory(user=user, work=book)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=UserFactory(), work=book)
    UserWorkFactory(user=user, work=BookFactory())


# ─── CollectionItem ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_collection_item_saves_valid_work(book):
    CollectionItemFactory(work=book)


@pytest.mark.django_db
def test_collection_item_rejects_missing_work():
    collection = CollectionFactory()
    item = CollectionItemFactory.build(collection=collection, work=BookFactory())
    item.work_object_id = 999_999
    with pytest.raises(ValidationError):
        item.save()


@pytest.mark.django_db(transaction=True)
def test_collection_item_unique_work_per_collection(book):
    collection = CollectionFactory()
    CollectionItemFactory(collection=collection, work=book)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            CollectionItemFactory(collection=collection, work=book)
    CollectionItemFactory(collection=CollectionFactory(), work=book)
    CollectionItemFactory(collection=collection, work=BookFactory())


# ─── Collection ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_collection_root_saves(user):
    CollectionFactory(user=user, parent=None)
    existing = CollectionFactory(user=user)
    existing.parent = None
    existing.save()


@pytest.mark.django_db
def test_collection_new_child_of_root_saves(user):
    root = CollectionFactory(user=user)
    CollectionFactory(user=user, parent=root)


@pytest.mark.django_db
def test_collection_self_parent_raises_on_save(user):
    node = CollectionFactory(user=user)
    node.parent = node
    with pytest.raises(ValidationError, match="своим родителем"):
        node.save()


@pytest.mark.django_db
def test_collection_descendant_as_parent_raises_on_save(user):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    grandchild = CollectionFactory(user=user, parent=child)

    root.parent = grandchild
    with pytest.raises(ValidationError, match="потомка"):
        root.save()

    root.refresh_from_db()
    root.parent = child
    with pytest.raises(ValidationError, match="потомка"):
        root.save()


@pytest.mark.django_db
def test_collection_sibling_and_move_up_save(user):
    root = CollectionFactory(user=user)
    sibling_a = CollectionFactory(user=user, parent=root)
    sibling_b = CollectionFactory(user=user, parent=root)
    grandchild = CollectionFactory(user=user, parent=sibling_a)

    sibling_a.parent = sibling_b
    sibling_a.save()

    grandchild.parent = root
    grandchild.save()


# ─── Lookup unique ───────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("factory", LOOKUP_FACTORIES)
def test_lookup_name_unique_is_case_sensitive(factory):
    obj = factory(name="Fantasy")
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            factory._meta.model.objects.create(name="Fantasy")
    factory._meta.model.objects.create(name="fantasy")
    factory(name="Sci-Fi")
    assert obj.name == "Fantasy"
