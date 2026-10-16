"""Tests for apps.vor_archives models."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import FilmTypeChoices, WorkRelationTypeChoices
from apps.vor_archives.models import (
    Collection,
    CollectionItem,
    Film,
    UserWork,
    WorkRelation,
)
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
@pytest.mark.parametrize("episode_count", [1, 10])
def test_film_tv_show_with_min_and_typical_episode_count_saves(episode_count):
    film = FilmFactory(tv=True, episode_count=episode_count)
    film.refresh_from_db()
    assert Film.objects.filter(pk=film.pk).exists()
    assert film.film_type == FilmTypeChoices.TV_SHOW
    assert film.episode_count == episode_count


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
    movie = Film.objects.get(title="Movie")
    show = Film.objects.get(title="Show")
    assert movie.film_type == FilmTypeChoices.MOVIE
    assert movie.episode_count is None
    assert show.film_type == FilmTypeChoices.TV_SHOW
    assert show.episode_count == 1


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


def _assert_relation(rel, source, target, relation_type):
    rel.refresh_from_db()
    assert WorkRelation.objects.filter(pk=rel.pk).exists()
    assert rel.relation_type == relation_type
    assert rel.source_object_id == source.pk
    assert rel.target_object_id == target.pk
    assert rel.source_content_type_id == _ct(source).id
    assert rel.target_content_type_id == _ct(target).id


@pytest.mark.django_db
def test_work_relation_valid_pairs_save(book, movie):
    sequel_target = BookFactory()
    other_target = FilmFactory()
    sequel = WorkRelationFactory(
        source=book,
        target=sequel_target,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )
    adaptation = WorkRelationFactory(
        source=book,
        target=movie,
        relation_type=WorkRelationTypeChoices.ADAPTATION,
    )
    other = WorkRelationFactory(
        source=book,
        target=other_target,
        relation_type=WorkRelationTypeChoices.OTHER,
    )
    _assert_relation(sequel, book, sequel_target, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(adaptation, book, movie, WorkRelationTypeChoices.ADAPTATION)
    _assert_relation(other, book, other_target, WorkRelationTypeChoices.OTHER)


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


@pytest.mark.django_db
def test_work_relation_same_direction_duplicate_raises_on_save(book):
    other = BookFactory()
    WorkRelationFactory(source=book, target=other)
    with pytest.raises(ValidationError):
        WorkRelation(
            source_content_type=_ct(book),
            source_object_id=book.pk,
            target_content_type=_ct(other),
            target_object_id=other.pk,
            relation_type=WorkRelationTypeChoices.REMAKE,
        ).save()


@pytest.mark.django_db(transaction=True)
def test_work_relation_same_direction_duplicate_hits_db_unique(book):
    other = BookFactory()
    existing = WorkRelationFactory(source=book, target=other)
    with pytest.raises(IntegrityError):
        WorkRelation.objects.bulk_create(
            [
                WorkRelation(
                    source_content_type=existing.source_content_type,
                    source_object_id=existing.source_object_id,
                    target_content_type=existing.target_content_type,
                    target_object_id=existing.target_object_id,
                    relation_type=WorkRelationTypeChoices.REMAKE,
                )
            ]
        )


@pytest.mark.django_db
def test_work_relation_shared_source_or_target_allowed(book):
    out_a = BookFactory()
    out_b = BookFactory()
    from_book_a = WorkRelationFactory(source=book, target=out_a)
    from_book_b = WorkRelationFactory(source=book, target=out_b)
    shared_target = BookFactory()
    in_a = BookFactory()
    in_b = BookFactory()
    to_shared_a = WorkRelationFactory(source=in_a, target=shared_target)
    to_shared_b = WorkRelationFactory(source=in_b, target=shared_target)

    _assert_relation(from_book_a, book, out_a, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(from_book_b, book, out_b, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(to_shared_a, in_a, shared_target, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(to_shared_b, in_b, shared_target, WorkRelationTypeChoices.SEQUEL)
    assert WorkRelation.objects.filter(source_object_id=book.pk).count() == 2
    assert WorkRelation.objects.filter(target_object_id=shared_target.pk).count() == 2


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
    ab = WorkRelationFactory(source=a, target=b)
    cd = WorkRelationFactory(source=c, target=d)
    bc = WorkRelationFactory(source=b, target=c)
    _assert_relation(ab, a, b, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(cd, c, d, WorkRelationTypeChoices.SEQUEL)
    _assert_relation(bc, b, c, WorkRelationTypeChoices.SEQUEL)
    assert WorkRelation.objects.count() == 3


# ─── UserWork ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [None, 1, 10])
def test_user_work_rating_bounds_save(book, user, rating):
    uw = UserWorkFactory(user=user, work=book, rating=rating)
    uw.refresh_from_db()
    assert UserWork.objects.filter(pk=uw.pk).exists()
    assert uw.user_id == user.pk
    assert uw.work == book
    assert uw.rating == rating


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [0, 11])
def test_user_work_rating_outside_bounds_raises(book, user, rating):
    with pytest.raises(ValidationError):
        UserWorkFactory(user=user, work=book, rating=rating)


@pytest.mark.django_db
@pytest.mark.parametrize("work_factory", [BookFactory, FilmFactory, GameFactory])
def test_user_work_accepts_each_work_type(user, work_factory):
    work = work_factory()
    uw = UserWorkFactory(user=user, work=work)
    uw.refresh_from_db()
    assert UserWork.objects.filter(pk=uw.pk).exists()
    assert uw.user_id == user.pk
    assert uw.work == work
    assert uw.work_content_type_id == _ct(work).id
    assert uw.work_object_id == work.pk


@pytest.mark.django_db
def test_user_work_rejects_missing_work(user, book):
    uw = UserWork(
        user=user,
        work_content_type=_ct(book),
        work_object_id=999_999,
    )
    with pytest.raises(ValidationError):
        uw.save()


@pytest.mark.django_db
def test_user_work_duplicate_raises_on_save(book, user):
    UserWorkFactory(user=user, work=book)
    with pytest.raises(ValidationError):
        UserWorkFactory(user=user, work=book)
    other_user = UserFactory()
    other_work = BookFactory()
    other_user_uw = UserWorkFactory(user=other_user, work=book)
    other_work_uw = UserWorkFactory(user=user, work=other_work)
    other_user_uw.refresh_from_db()
    other_work_uw.refresh_from_db()
    assert other_user_uw.user_id == other_user.pk
    assert other_user_uw.work == book
    assert other_work_uw.user_id == user.pk
    assert other_work_uw.work == other_work


@pytest.mark.django_db(transaction=True)
def test_user_work_duplicate_hits_db_unique(book, user):
    existing = UserWorkFactory(user=user, work=book)
    with pytest.raises(IntegrityError):
        UserWork.objects.bulk_create(
            [
                UserWork(
                    user=user,
                    work_content_type=existing.work_content_type,
                    work_object_id=existing.work_object_id,
                )
            ]
        )


@pytest.mark.django_db
def test_next_position_returns_one_for_first_work(user):
    assert UserWork.next_position(user) == 0


@pytest.mark.django_db
def test_next_position_increments_for_each_existing(user, book, movie):
    UserWork.objects.create(user=user, work=book)
    UserWork.objects.create(user=user, work=movie)
    assert UserWork.next_position(user) == 2


@pytest.mark.django_db
def test_next_position_is_per_user(user, book, movie):
    other_user = UserFactory()
    UserWork.objects.create(user=user, work=book)
    UserWork.objects.create(user=other_user, work=movie)
    assert UserWork.next_position(user) == 1
    assert UserWork.next_position(other_user) == 1


@pytest.mark.django_db
def test_save_assigns_unique_position_on_create(user, book, movie):
    uw1 = UserWork.objects.create(user=user, work=book)
    uw2 = UserWork.objects.create(user=user, work=movie)
    assert uw1.order_position == 0
    assert uw2.order_position == 1


@pytest.mark.django_db
def test_save_does_not_override_explicit_position(user, book):
    uw = UserWork.objects.create(user=user, work=book, order_position=99)
    assert uw.order_position == 99


@pytest.mark.django_db
def test_save_does_not_reassign_on_update(user, book):
    uw = UserWork.objects.create(user=user, work=book)
    uw.order_position = 5
    uw.save()
    uw.refresh_from_db()
    assert uw.order_position == 5


# ─── CollectionItem ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_collection_item_saves_valid_work(book):
    item = CollectionItemFactory(work=book)
    item.refresh_from_db()
    assert CollectionItem.objects.filter(pk=item.pk).exists()
    assert item.work == book
    assert item.collection_id is not None


@pytest.mark.django_db
def test_collection_item_rejects_missing_work():
    collection = CollectionFactory()
    item = CollectionItemFactory.build(collection=collection, work=BookFactory())
    item.work_object_id = 999_999
    with pytest.raises(ValidationError):
        item.save()


@pytest.mark.django_db
def test_collection_item_duplicate_raises_on_save(book):
    collection = CollectionFactory()
    CollectionItemFactory(collection=collection, work=book)
    with pytest.raises(ValidationError):
        CollectionItemFactory(collection=collection, work=book)
    other_collection = CollectionFactory()
    other_work = BookFactory()
    other_collection_item = CollectionItemFactory(
        collection=other_collection, work=book
    )
    other_work_item = CollectionItemFactory(collection=collection, work=other_work)
    other_collection_item.refresh_from_db()
    other_work_item.refresh_from_db()
    assert other_collection_item.collection_id == other_collection.pk
    assert other_collection_item.work == book
    assert other_work_item.collection_id == collection.pk
    assert other_work_item.work == other_work


@pytest.mark.django_db(transaction=True)
def test_collection_item_duplicate_hits_db_unique(book):
    collection = CollectionFactory()
    existing = CollectionItemFactory(collection=collection, work=book)
    with pytest.raises(IntegrityError):
        CollectionItem.objects.bulk_create(
            [
                CollectionItem(
                    collection=collection,
                    work_content_type=existing.work_content_type,
                    work_object_id=existing.work_object_id,
                )
            ]
        )


# ─── Collection ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_collection_root_saves(user):
    created = CollectionFactory(user=user, parent=None)
    created.refresh_from_db()
    assert Collection.objects.filter(pk=created.pk).exists()
    assert created.parent is None
    assert created.user_id == user.pk

    existing = CollectionFactory(user=user)
    existing.parent = None
    existing.save()
    existing.refresh_from_db()
    assert existing.parent is None
    assert existing.user_id == user.pk


@pytest.mark.django_db
def test_collection_new_child_of_root_saves(user):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    child.refresh_from_db()
    assert Collection.objects.filter(pk=child.pk).exists()
    assert child.parent_id == root.pk
    assert child.user_id == user.pk


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
def test_collection_sibling_reparent_saves(user):
    root = CollectionFactory(user=user)
    sibling_a = CollectionFactory(user=user, parent=root)
    sibling_b = CollectionFactory(user=user, parent=root)

    sibling_a.refresh_from_db()
    sibling_b.refresh_from_db()
    sibling_a.parent = sibling_b
    sibling_a.save()
    sibling_a.refresh_from_db()
    assert sibling_a.parent_id == sibling_b.pk


@pytest.mark.django_db
def test_collection_move_up_to_root_saves(user):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    grandchild = CollectionFactory(user=user, parent=child)

    grandchild.refresh_from_db()
    root.refresh_from_db()
    grandchild.parent = root
    grandchild.save()
    grandchild.refresh_from_db()
    assert grandchild.parent_id == root.pk


# ─── Lookup unique ───────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("factory", LOOKUP_FACTORIES)
def test_lookup_name_unique_is_case_sensitive(factory):
    obj = factory(name="Fantasy")
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            factory._meta.model.objects.create(name="Fantasy")
    model = factory._meta.model
    model.objects.create(name="fantasy")
    factory(name="Sci-Fi")
    obj.refresh_from_db()
    assert obj.name == "Fantasy"
    assert model.objects.filter(name="Fantasy").exists()
    assert model.objects.filter(name="fantasy").exists()
    assert model.objects.filter(name="Sci-Fi").exists()
