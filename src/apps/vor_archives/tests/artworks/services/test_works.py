"""Tests for apps.vor_archives.artworks.services.works."""

from decimal import Decimal

import pytest
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from apps.users.tests.factories import UserFactory
from apps.vor_archives.artworks.services import (
    attach_work,
    clamp_progress_for_work,
    delete_user_works,
    get_user_work,
    get_work,
    list_user_works,
    orphan_works,
    reorder_user_works,
    sync_work_relations,
    user_has_work,
    user_owned_work_ids,
    work_relation_items,
    work_type_key,
)
from apps.vor_archives.artworks.services.utils import work_key
from apps.vor_archives.artworks.services.works import (
    collection_scope_keys,
    get_work_model,
    relation_label,
)
from apps.vor_archives.constants import (
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
)
from apps.vor_archives.models import (
    Book,
    CompletionRecord,
    FeedItem,
    Film,
    Game,
    UserWork,
    WorkRelation,
)
from apps.vor_archives.tests.factories import (
    BookFactory,
    CollectionFactory,
    CollectionItemFactory,
    FilmFactory,
    PlatformFactory,
    UserWorkFactory,
    WorkRelationFactory,
)
from ...conftest import ALL_STATUSES

# ─── collection_scope_keys ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_collection_scope_keys_direct_only(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    item_book = CollectionItemFactory(collection=root, work=book)
    CollectionItemFactory(collection=child, work=movie)

    keys = collection_scope_keys(root, include_descendants=False)

    assert keys == {work_key(item_book)}


@pytest.mark.django_db
def test_collection_scope_keys_with_descendants(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    item_book = CollectionItemFactory(collection=root, work=book)
    item_movie = CollectionItemFactory(collection=child, work=movie)

    keys = collection_scope_keys(root, include_descendants=True)

    assert keys == {work_key(item_book), work_key(item_movie)}


# ─── get_work_model / get_work / work_type_key ──────────────────────────────


def test_get_work_model_returns_correct_classes():
    assert get_work_model("book") is Book
    assert get_work_model("film") is Film
    assert get_work_model("game") is Game


def test_get_work_model_raises_for_unknown():
    with pytest.raises(ValueError):
        get_work_model("nope")


@pytest.mark.django_db
def test_get_work_returns_object(book):
    assert get_work("book", book.pk) == book


@pytest.mark.django_db
def test_get_work_raises_404_for_missing():
    with pytest.raises(Http404):
        get_work("book", 999999)


def test_get_work_raises_value_error_for_unknown_type():
    with pytest.raises(ValueError):
        get_work("nope", 1)


@pytest.mark.django_db
def test_work_type_key(book, movie, game):
    assert work_type_key(book) == "book"
    assert work_type_key(movie) == "film"
    assert work_type_key(game) == "game"


# ─── list_user_works ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_list_user_works_empty_without_types(user, book):
    UserWorkFactory(user=user, work=book)

    assert list_user_works(user, {}) == []


@pytest.mark.django_db
def test_list_user_works_basic(user, book):
    uw = UserWorkFactory(user=user, work=book)

    result = list_user_works(
        user,
        {
            "types": ["book"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
        },
    )

    assert result == [uw]


@pytest.mark.django_db
def test_list_user_works_unknown_collection_returns_empty(user, book):
    UserWorkFactory(user=user, work=book)

    result = list_user_works(user, {"types": ["book"], "collection_id": 999999})

    assert result == []


@pytest.mark.django_db
def test_list_user_works_foreign_collection_returns_empty(user, book):
    other = UserFactory()
    foreign_collection = CollectionFactory(user=other)
    UserWorkFactory(user=user, work=book)

    result = list_user_works(
        user, {"types": ["book"], "collection_id": foreign_collection.pk}
    )

    assert result == []


@pytest.mark.django_db
def test_list_user_works_collection_filter_excludes_outsiders(user, book, movie):
    collection = CollectionFactory(user=user)
    CollectionItemFactory(collection=collection, work=book)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "collection_id": collection.pk,
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == book.pk


@pytest.mark.django_db
def test_list_user_works_includes_collection_descendants(user, book, movie):
    root = CollectionFactory(user=user)
    child = CollectionFactory(user=user, parent=root)
    CollectionItemFactory(collection=child, work=movie)
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=movie)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "collection_id": root.pk,
        },
    )

    assert len(result) == 1
    assert result[0].work_object_id == movie.pk


@pytest.mark.django_db
def test_list_user_works_sorted_by_title(user):
    book = BookFactory(title="Zeta")
    film = FilmFactory(title="Alpha")
    UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=user, work=film)

    result = list_user_works(
        user,
        {
            "types": ["book", "film"],
            "statuses": ALL_STATUSES,
            "all_statuses": ALL_STATUSES,
            "sort": "title",
            "sort_asc": True,
        },
    )

    assert [uw.work.title for uw in result] == ["Alpha", "Zeta"]


# ─── get_user_work / user_has_work / user_owned_work_ids ─────────────────────


@pytest.mark.django_db
def test_get_user_work_returns_owned(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert get_user_work(user, book) == uw


@pytest.mark.django_db
def test_get_user_work_returns_none_when_not_owned(user, book):
    assert get_user_work(user, book) is None


@pytest.mark.django_db
def test_get_user_work_ignores_other_users(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    assert get_user_work(user, book) is None


@pytest.mark.django_db
def test_user_has_work(user, book):
    assert user_has_work(user, book) is False
    UserWorkFactory(user=user, work=book)
    assert user_has_work(user, book) is True


@pytest.mark.django_db
def test_user_owned_work_ids(user, book, movie):
    UserWorkFactory(user=user, work=book)

    assert list(user_owned_work_ids(user, "book")) == [book.pk]
    assert list(user_owned_work_ids(user, "film")) == []


@pytest.mark.django_db
def test_user_owned_work_ids_ignores_other_users(user, book):
    other = UserFactory()
    UserWorkFactory(user=other, work=book)

    assert list(user_owned_work_ids(user, "book")) == []


# ─── reorder_user_works (moved from tests/test_services.py) ─────────────────


@pytest.mark.django_db
def test_reorder_normalizes_non_unique_positions(user, book, movie):
    uw1 = UserWork.objects.create(user=user, work=book)
    uw2 = UserWork.objects.create(user=user, work=movie)
    UserWork.objects.filter(pk__in=[uw1.pk, uw2.pk]).update(order_position=0)

    reorder_user_works(user, [uw1.pk, uw2.pk])

    uw1.refresh_from_db()
    uw2.refresh_from_db()
    assert uw1.order_position == 0
    assert uw2.order_position == 1


@pytest.mark.django_db
def test_reorder_normalizes_gaps_in_positions(user, book, movie, game):
    uw1 = UserWork.objects.create(user=user, work=book, order_position=5)
    uw2 = UserWork.objects.create(user=user, work=movie, order_position=10)
    uw3 = UserWork.objects.create(user=user, work=game, order_position=15)

    reorder_user_works(user, [uw1.pk, uw2.pk, uw3.pk])

    uw1.refresh_from_db()
    uw2.refresh_from_db()
    uw3.refresh_from_db()
    assert (uw1.order_position, uw2.order_position, uw3.order_position) == (0, 1, 2)


@pytest.mark.django_db
def test_reorder_ignores_foreign_ids(user, book):
    other_user = UserFactory()
    uw = UserWork.objects.create(user=user, work=book)
    foreign = UserWork.objects.create(user=other_user, work=BookFactory())

    result = reorder_user_works(user, [uw.pk, foreign.pk])

    assert result == 1
    foreign.refresh_from_db()
    assert foreign.order_position == 0


@pytest.mark.django_db
def test_reorder_empty_list_returns_zero(user):
    assert reorder_user_works(user, []) == 0


# ─── orphan_works ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_orphan_works_single_owner(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert orphan_works([uw]) == [book]


@pytest.mark.django_db
def test_orphan_works_shared_is_not_orphan(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=other, work=book)

    assert orphan_works([uw]) == []


@pytest.mark.django_db
def test_orphan_works_empty_input():
    assert orphan_works([]) == []


@pytest.mark.django_db
def test_orphan_works_deduplicates(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert orphan_works([uw, uw]) == [book]


@pytest.mark.django_db
def test_orphan_works_multiple(user, book, movie):
    uw_book = UserWorkFactory(user=user, work=book)
    uw_movie = UserWorkFactory(user=user, work=movie)

    assert set(orphan_works([uw_book, uw_movie])) == {book, movie}


# ─── delete_user_works ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_delete_user_works_removes_userwork(user, book):
    uw = UserWorkFactory(user=user, work=book)

    assert delete_user_works(user, [uw.pk]) == 1
    assert not UserWork.objects.filter(pk=uw.pk).exists()


@pytest.mark.django_db
def test_delete_user_works_deletes_orphan_work(user, book):
    uw = UserWorkFactory(user=user, work=book)

    delete_user_works(user, [uw.pk])

    assert not Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_delete_user_works_keeps_shared_work(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    UserWorkFactory(user=other, work=book)

    delete_user_works(user, [uw.pk])

    assert Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_delete_user_works_ignores_foreign_ids(user, book):
    other = UserFactory()
    uw = UserWorkFactory(user=user, work=book)
    foreign = UserWorkFactory(user=other, work=BookFactory())

    assert delete_user_works(user, [uw.pk, foreign.pk]) == 1
    assert UserWork.objects.filter(pk=foreign.pk).exists()


@pytest.mark.django_db
def test_delete_user_works_empty_list(user):
    assert delete_user_works(user, []) == 0


@pytest.mark.django_db
def test_delete_user_works_removes_feed_items_and_completion_records(user, book):
    uw = UserWorkFactory(user=user, work=book)
    uw.status = UserWorkStatusChoices.COMPLETED
    uw.save()

    assert FeedItem.objects.filter(user_work_id=uw.pk).exists()
    assert CompletionRecord.objects.filter(user_work_id=uw.pk).exists()

    delete_user_works(user, [uw.pk])

    assert not FeedItem.objects.filter(user_work_id=uw.pk).exists()
    # CompletionRecord cascades via FK CASCADE
    assert not CompletionRecord.objects.filter(user_work_id=uw.pk).exists()


# ─── attach_work ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_attach_work_creates_new(user, book):
    uw, created = attach_work(user, "book", book.pk)

    assert created is True
    assert uw.user == user
    assert uw.work_object_id == book.pk


@pytest.mark.django_db
def test_attach_work_returns_existing(user, book):
    existing = UserWorkFactory(user=user, work=book)

    uw, created = attach_work(user, "book", book.pk)

    assert created is False
    assert uw.pk == existing.pk


@pytest.mark.django_db
def test_attach_work_first_uw_gets_position_zero(user, book):
    uw, _ = attach_work(user, "book", book.pk)

    assert uw.order_position == 0


@pytest.mark.django_db
def test_attach_work_increments_position(user, movie, book):
    UserWorkFactory(user=user, work=movie)

    uw, _ = attach_work(user, "book", book.pk)

    assert uw.order_position == 1


@pytest.mark.django_db
def test_attach_work_respects_explicit_order_position(user, book):
    uw, _ = attach_work(user, "book", book.pk, cleaned_user_data={"order_position": 42})

    assert uw.order_position == 42


@pytest.mark.django_db
def test_attach_work_applies_cleaned_user_data(user, book):
    platform = PlatformFactory()

    uw, created = attach_work(
        user,
        "book",
        book.pk,
        cleaned_user_data={
            "status": UserWorkStatusChoices.COMPLETED,
            "rating": 9,
            "owned_platforms": [platform],
        },
    )

    assert created is True
    assert uw.status == UserWorkStatusChoices.COMPLETED
    assert uw.rating == 9
    assert list(uw.owned_platforms.all()) == [platform]


@pytest.mark.django_db
def test_attach_work_does_not_touch_platforms_on_existing(user, book):
    UserWorkFactory(user=user, work=book)
    platform = PlatformFactory()

    uw, created = attach_work(
        user, "book", book.pk, cleaned_user_data={"owned_platforms": [platform]}
    )

    assert created is False
    assert list(uw.owned_platforms.all()) == []


@pytest.mark.django_db
def test_attach_work_unknown_type_raises(user):
    with pytest.raises(ValueError):
        attach_work(user, "nope", 1)


@pytest.mark.django_db
def test_attach_work_missing_work_raises_404(user):
    with pytest.raises(Http404):
        attach_work(user, "book", 999999)


# ─── relation_label ──────────────────────────────────────────────────────────


def test_relation_label_sequel_both_directions():
    assert relation_label(WorkRelationTypeChoices.SEQUEL, "out") == "Продолжение"
    assert relation_label(WorkRelationTypeChoices.SEQUEL, "in") == "Предыстория"


def test_relation_label_unknown_type_falls_back():
    assert relation_label("unknown", "out") == "Связано"
    assert relation_label("unknown", "in") == "Связано"


# ─── work_relation_items ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_work_relation_items_empty(book):
    assert work_relation_items(book) == []


@pytest.mark.django_db
def test_work_relation_items_outgoing(book):
    sequel = BookFactory(title="Sequel")
    rel = WorkRelationFactory(
        source=book, target=sequel, relation_type=WorkRelationTypeChoices.SEQUEL
    )

    items = work_relation_items(book)

    assert len(items) == 1
    item = items[0]
    assert set(item.keys()) == {
        "id",
        "title",
        "cover_url",
        "label",
        "icon",
        "type_key",
        "work_id",
        "relation_type",
        "direction",
    }
    assert item["id"] == rel.pk
    assert item["title"] == "Sequel"
    assert item["work_id"] == sequel.pk
    assert item["type_key"] == "book"
    assert item["direction"] == "out"
    assert item["label"] == "Продолжение"


@pytest.mark.django_db
def test_work_relation_items_incoming(book):
    prequel = BookFactory(title="Prequel")
    rel = WorkRelationFactory(
        source=prequel, target=book, relation_type=WorkRelationTypeChoices.SEQUEL
    )

    items = work_relation_items(book)

    assert len(items) == 1
    assert items[0]["id"] == rel.pk
    assert items[0]["work_id"] == prequel.pk
    assert items[0]["direction"] == "in"
    assert items[0]["label"] == "Предыстория"


@pytest.mark.django_db
def test_work_relation_items_both_directions(book):
    sequel = BookFactory()
    prequel = BookFactory()
    WorkRelationFactory(source=book, target=sequel)
    WorkRelationFactory(source=prequel, target=book)

    items = work_relation_items(book)

    assert len(items) == 2
    assert {item["direction"] for item in items} == {"out", "in"}


# ─── clamp_progress_for_work ────────────────────────────────────────────────


@pytest.mark.django_db
def test_clamp_progress_book_caps_at_pages(user, book):
    book.pages = 100
    book.save()
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("150"))

    clamp_progress_for_work(book)

    uw.refresh_from_db()
    assert uw.progress == Decimal("100")


@pytest.mark.django_db
def test_clamp_progress_book_leaves_lower_untouched(user, book):
    book.pages = 100
    book.save()
    uw = UserWorkFactory(user=user, work=book, progress=Decimal("50"))

    clamp_progress_for_work(book)

    uw.refresh_from_db()
    assert uw.progress == Decimal("50")


@pytest.mark.django_db
def test_clamp_progress_movie_uses_duration(user, movie):
    movie.duration_minutes = 120
    movie.save()
    uw = UserWorkFactory(user=user, work=movie, progress=Decimal("200"))

    clamp_progress_for_work(movie)

    uw.refresh_from_db()
    assert uw.progress == Decimal("120")


@pytest.mark.django_db
def test_clamp_progress_tv_show_uses_episode_count(user, tv_show):
    uw = UserWorkFactory(user=user, work=tv_show, progress=Decimal("100"))

    clamp_progress_for_work(tv_show)

    uw.refresh_from_db()
    assert uw.progress == Decimal("10")


@pytest.mark.django_db
def test_clamp_progress_game_does_nothing(user, game):
    uw = UserWorkFactory(user=user, work=game, progress=Decimal("9999"))

    clamp_progress_for_work(game)

    uw.refresh_from_db()
    assert uw.progress == Decimal("9999")


# ─── sync_work_relations ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_sync_work_relations_creates_new_outgoing(book):
    target = BookFactory()

    sync_work_relations(
        book,
        [
            {
                "type_key": "book",
                "work_id": target.pk,
                "relation_type": WorkRelationTypeChoices.SEQUEL,
            }
        ],
    )

    book_ct = ContentType.objects.get_for_model(Book)
    assert WorkRelation.objects.filter(
        source_content_type=book_ct,
        source_object_id=book.pk,
        target_content_type=book_ct,
        target_object_id=target.pk,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    ).exists()


@pytest.mark.django_db
def test_sync_work_relations_updates_existing_type(book):
    other = BookFactory()
    rel = WorkRelationFactory(
        source=book,
        target=other,
        relation_type=WorkRelationTypeChoices.OTHER,
    )

    sync_work_relations(
        book,
        [{"id": rel.pk, "relation_type": WorkRelationTypeChoices.SEQUEL}],
    )

    rel.refresh_from_db()
    assert rel.relation_type == WorkRelationTypeChoices.SEQUEL


@pytest.mark.django_db
def test_sync_work_relations_preserves_listed_relation(book):
    other = BookFactory()
    rel = WorkRelationFactory(
        source=book,
        target=other,
        relation_type=WorkRelationTypeChoices.SEQUEL,
    )

    sync_work_relations(
        book,
        [{"id": rel.pk, "relation_type": WorkRelationTypeChoices.SEQUEL}],
    )

    assert WorkRelation.objects.filter(pk=rel.pk).exists()


@pytest.mark.django_db
def test_sync_work_relations_deletes_unlisted_outgoing(book):
    other = BookFactory()
    rel = WorkRelationFactory(source=book, target=other)

    sync_work_relations(book, [])

    assert not WorkRelation.objects.filter(pk=rel.pk).exists()


@pytest.mark.django_db
def test_sync_work_relations_deletes_unlisted_incoming(book):
    """Documents current behavior: incoming relations are also removed."""
    other = BookFactory()
    rel = WorkRelationFactory(source=other, target=book)

    sync_work_relations(book, [])

    assert not WorkRelation.objects.filter(pk=rel.pk).exists()


@pytest.mark.django_db
def test_sync_work_relations_skips_self_relation(book):
    sync_work_relations(
        book,
        [
            {
                "type_key": "book",
                "work_id": book.pk,
                "relation_type": WorkRelationTypeChoices.SEQUEL,
            }
        ],
    )

    book_ct = ContentType.objects.get_for_model(Book)
    assert not WorkRelation.objects.filter(
        source_content_type=book_ct,
        source_object_id=book.pk,
        target_content_type=book_ct,
        target_object_id=book.pk,
    ).exists()


@pytest.mark.django_db
def test_sync_work_relations_skips_items_without_payload(book):
    sync_work_relations(book, [{}])

    assert not WorkRelation.objects.exists()


@pytest.mark.django_db
def test_sync_work_relations_ignores_unknown_relation_id(book):
    sync_work_relations(book, [{"id": 999999}])

    # Only risk is that no relations were deleted erroneously; nothing to assert about existence.
    assert not WorkRelation.objects.exists()


@pytest.mark.django_db
def test_sync_work_relations_invalid_target_raises_404(book):
    with pytest.raises(Http404):
        sync_work_relations(book, [{"type_key": "book", "work_id": 999999}])
