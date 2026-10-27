from django.db import transaction
from django.db.models import Count, Q, prefetch_related_objects
from django.shortcuts import get_object_or_404

from apps.vor_archives.constants import WORK_TYPE_ICONS, WorkRelationTypeChoices
from apps.vor_archives.models import (
    Collection,
    CollectionItem,
    FeedItem,
    UserWork,
    WorkRelation,
)
from apps.vor_archives.registry import get_work_model
from .content_types import ct_for, ct_for_type
from .progress import clamp_progress, clamp_progress_for_work
from .queries import load_filtered_user_works, sort_user_works
from .utils import work_key, relation_cover_url

from apps.vor_archives.artworks.constants import RELATION_LABELS


class AlreadyAttached(Exception):
    """Raised when the user already owns the work being attached."""

    def __init__(self, work):
        self.work = work
        super().__init__("already")


## TODO: Move to collections.py once refactor list_user_works
def collection_scope_keys(collection, include_descendants=True):
    qs = CollectionItem.objects.filter(collection=collection)
    if include_descendants:
        descendant_ids = collection.get_descendants().values_list("pk", flat=True)
        qs = CollectionItem.objects.filter(
            collection_id__in=[collection.pk, *descendant_ids]
        )
    return {work_key(item) for item in qs}


## TODO: Separate to two functions
def list_user_works(user, params):
    items = load_filtered_user_works(user, params)
    collection_id = params.get("collection_id")
    if collection_id:
        collection = Collection.objects.filter(user=user, pk=collection_id).first()
        if collection is None:
            return []
        keys = collection_scope_keys(collection, include_descendants=True)
        items = [user_work for user_work in items if work_key(user_work) in keys]
    return sort_user_works(items, params)


def get_work(type_key: str, work_id: int):
    return get_object_or_404(get_work_model(type_key), pk=work_id)


def work_type_key(work) -> str:
    return work._meta.model_name


def get_user_work(user, work):
    return UserWork.objects.filter(
        user=user,
        work_content_type=ct_for(work),
        work_object_id=work.pk,
    ).first()


def user_has_work(user, work) -> bool:
    return get_user_work(user, work) is not None


def user_owned_work_ids(user, type_key):
    return UserWork.objects.filter(
        user=user,
        work_content_type=ct_for_type(type_key),
    ).values_list("work_object_id", flat=True)


@transaction.atomic
def save_work_with_relations(work_form, relations, user_work=None):
    """Atomically save work form, relations, and prune stale UserWork data."""
    saved_work = work_form.save()

    if work_form.data.get("cover_clear") == "1" and not work_form.files.get("cover"):
        if saved_work.cover:
            saved_work.cover.delete(save=False)
        saved_work.cover = None
        saved_work.save(update_fields=["cover"])

    sync_work_relations(saved_work, relations)
    clamp_progress_for_work(saved_work)

    type_key = work_type_key(saved_work)
    if type_key == "game" and user_work is not None:
        valid_ids = set(saved_work.platforms.values_list("pk", flat=True))
        stale_ids = [
            pk
            for pk in user_work.owned_platforms.values_list("pk", flat=True)
            if pk not in valid_ids
        ]
        if stale_ids:
            user_work.owned_platforms.remove(*stale_ids)

    return saved_work


def reorder_user_works(user, ids):
    existing = {
        user_work.pk: user_work
        for user_work in UserWork.objects.filter(user=user, pk__in=ids)
    }
    ordered = [existing[uw_id] for uw_id in ids if uw_id in existing]
    to_update = []
    for position, user_work in enumerate(ordered):
        if user_work.order_position != position:
            user_work.order_position = position
            to_update.append(user_work)
    if to_update:
        UserWork.objects.bulk_update(to_update, ["order_position"])
    return len(ordered)


def orphan_works(user_works):
    """Произведения, у которых после удаления этих UserWork не останется привязок."""
    user_works = list(user_works)
    if not user_works:
        return []

    keys = {(uw.work_content_type_id, uw.work_object_id) for uw in user_works}
    q = Q()
    for ct_id, obj_id in keys:
        q |= Q(work_content_type_id=ct_id, work_object_id=obj_id)

    counts = {
        (row["work_content_type_id"], row["work_object_id"]): row["n"]
        for row in UserWork.objects.filter(q)
        .values("work_content_type_id", "work_object_id")
        .annotate(n=Count("id"))
    }

    orphans = []
    seen = set()
    for uw in user_works:
        key = (uw.work_content_type_id, uw.work_object_id)
        if key in seen:
            continue
        seen.add(key)
        if counts.get(key, 0) <= 1 and uw.work is not None:
            orphans.append(uw.work)
    return orphans


@transaction.atomic
def delete_user_works(user, ids):
    qs = UserWork.objects.filter(user=user, pk__in=ids).select_related(
        "work_content_type"
    )
    user_works = list(qs)
    if not user_works:
        return 0
    prefetch_related_objects(user_works, "work")

    orphans = orphan_works(user_works)
    orphan_keys = {
        (uw.work_content_type_id, uw.work_object_id)
        for uw in user_works
        if uw.work in orphans
    }
    orphan_uw_ids = [
        uw.pk
        for uw in user_works
        if (uw.work_content_type_id, uw.work_object_id) in orphan_keys
    ]
    if orphan_uw_ids:
        FeedItem.objects.filter(user_work_id__in=orphan_uw_ids).delete()

    UserWork.objects.filter(pk__in=[uw.pk for uw in user_works]).delete()
    for work in orphans:
        work.delete()
    return len(user_works)


def _attach_work(user, work, cleaned_user_data=None):
    """Create UserWork for a work instance. Internal helper.

    cleaned_user_data may contain status, rating, progress, order_position
    and owned_platforms (m2m, set after creation).
    """
    defaults = {}
    m2m_platforms = None
    if cleaned_user_data:
        for key, value in cleaned_user_data.items():
            if key == "owned_platforms":
                m2m_platforms = value
            else:
                defaults[key] = value
    if "order_position" not in defaults:
        defaults["order_position"] = UserWork.next_position(user)
    user_work, created = UserWork.objects.get_or_create(
        user=user,
        work_content_type=ct_for(work),
        work_object_id=work.pk,
        defaults=defaults,
    )
    if created and m2m_platforms is not None:
        user_work.owned_platforms.set(m2m_platforms)
    return user_work, created


@transaction.atomic
def attach_work_from_form(user, form):
    """Attach a work using validated AttachWorkForm data.

    Raises AlreadyAttached if the user already owns the work.
    Clamps progress to the work maximum.
    """
    type_key = form.cleaned_data["work_type"]
    work = get_work(type_key, form.cleaned_data["work_id"])
    if user_has_work(user, work):
        raise AlreadyAttached(work)
    original_progress = form.cleaned_data["progress"]
    user_work, created = _attach_work(
        user,
        work,
        {
            "status": form.cleaned_data["status"],
            "rating": form.cleaned_data["rating"],
            "progress": original_progress,
        },
    )
    if created:
        clamp_progress(user_work)
        if user_work.progress != original_progress:
            user_work.save(update_fields=["progress"])
    return user_work, created


def relation_label(relation_type, direction="out"):
    outgoing_label, incoming_label = RELATION_LABELS.get(
        relation_type, ("Связано", "Связано")
    )
    return outgoing_label if direction == "out" else incoming_label


def _relation_item(work, label, relation, direction):
    return {
        "id": relation.pk,
        "title": work.title,
        "cover_url": relation_cover_url(work),
        "label": label,
        "icon": WORK_TYPE_ICONS.get(work._meta.model_name, "bi bi-collection"),
        "type_key": work._meta.model_name,
        "work_id": work.pk,
        "relation_type": relation.relation_type,
        "direction": direction,
    }


def work_relation_items(work):
    """Связанные произведения с подписью относительно текущего."""
    ct = ct_for(work)
    items = []
    outgoing = WorkRelation.objects.filter(
        source_content_type=ct,
        source_object_id=work.pk,
    )
    incoming = WorkRelation.objects.filter(
        target_content_type=ct,
        target_object_id=work.pk,
    )
    for relation in outgoing:
        other = relation.target
        if other is None:
            continue
        items.append(
            _relation_item(
                other, relation_label(relation.relation_type, "out"), relation, "out"
            )
        )
    for relation in incoming:
        other = relation.source
        if other is None:
            continue
        items.append(
            _relation_item(
                other, relation_label(relation.relation_type, "in"), relation, "in"
            )
        )
    return items


@transaction.atomic
def sync_work_relations(work, items):
    ct = ct_for(work)
    keep_ids = []
    new_items = []
    for item in items:
        relation_id = item.get("id")
        relation_type = item.get("relation_type") or WorkRelationTypeChoices.OTHER
        if relation_id:
            relation = (
                WorkRelation.objects.filter(pk=relation_id)
                .filter(
                    Q(source_content_type=ct, source_object_id=work.pk)
                    | Q(target_content_type=ct, target_object_id=work.pk)
                )
                .first()
            )
            if relation is None:
                continue
            if relation.relation_type != relation_type:
                relation.relation_type = relation_type
                relation.save()
            keep_ids.append(relation.pk)
            continue
        new_items.append(item)
    WorkRelation.objects.filter(
        Q(source_content_type=ct, source_object_id=work.pk)
        | Q(target_content_type=ct, target_object_id=work.pk)
    ).exclude(pk__in=keep_ids).delete()
    for item in new_items:
        type_key = item.get("type_key")
        work_id = item.get("work_id")
        relation_type = item.get("relation_type") or WorkRelationTypeChoices.OTHER
        if not type_key or not work_id:
            continue
        target = get_work(type_key, work_id)
        if target.pk == work.pk and work_type_key(target) == work_type_key(work):
            continue
        target_ct = ct_for_type(type_key)
        relation = WorkRelation(
            source_content_type=ct,
            source_object_id=work.pk,
            target_content_type=target_ct,
            target_object_id=target.pk,
            relation_type=relation_type,
        )
        relation.save()
