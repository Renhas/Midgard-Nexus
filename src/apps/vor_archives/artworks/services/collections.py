from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from mptt.utils import get_cached_trees

from apps.vor_archives.models import (
    Collection,
    CollectionItem,
    UserWork,
)

from .utils import work_key
from .queries import load_filtered_user_works, sort_user_works


def get_user_collection(user, pk):
    return get_object_or_404(Collection, user=user, pk=pk)


def get_user_collection_trees(user):
    return get_cached_trees(Collection.objects.filter(user=user))


def next_collection_order(user, parent=None):
    current = Collection.objects.filter(user=user, parent=parent).aggregate(
        Max("order")
    )
    return (current["order__max"] or 0) + 1


def next_collection_item_order(collection):
    current = collection.items.aggregate(Max("order"))
    return (current["order__max"] or 0) + 1


def create_collection(user, name, parent=None):
    name = (name or "").strip()
    if not name:
        raise ValidationError("Укажите название коллекции.")
    collection = Collection(
        user=user,
        name=name,
        parent=parent,
        order=next_collection_order(user, parent),
    )
    collection.save()
    return collection


def rename_collection(user, pk, name):
    name = (name or "").strip()
    if not name:
        raise ValidationError("Укажите название коллекции.")
    collection = get_user_collection(user, pk)
    collection.name = name
    collection.save(update_fields=["name"])
    return collection


def delete_collection(user, pk):
    collection = get_user_collection(user, pk)
    collection.delete()


def move_collection(user, collection_id, parent_id, sibling_ids):
    collection = get_user_collection(user, collection_id)
    parent = get_user_collection(user, parent_id) if parent_id else None
    if parent is not None:
        if parent.pk == collection.pk:
            raise ValidationError("Объект не может быть своим родителем.")
        if parent.pk in collection.get_descendants().values_list("pk", flat=True):
            raise ValidationError("Нельзя установить потомка в качестве родителя.")

    with transaction.atomic():
        if parent is not None and collection.parent_id != parent.pk:
            collection.move_to(parent, "last-child")
        elif parent is None and collection.parent_id is not None:
            other_root = (
                Collection.objects.filter(user=user, parent=None)
                .exclude(pk=collection.pk)
                .first()
            )
            if other_root is not None:
                collection.move_to(other_root, "right")
            else:  # pragma: no cover - unreachable with valid MPTT tree
                collection.parent = None
                collection.save()

        ordered_ids = []
        for raw in sibling_ids or []:
            try:
                ordered_ids.append(int(raw))
            except (TypeError, ValueError):
                continue
        siblings = list(Collection.objects.filter(user=user, parent=parent))
        by_id = {node.pk: node for node in siblings}
        ordered = [by_id[pk] for pk in ordered_ids if pk in by_id]
        leftover = [
            node for node in siblings if node.pk not in {pk for pk in ordered_ids}
        ]
        ordered.extend(leftover)
        for index, node in enumerate(ordered):
            node.order = index
        if ordered:
            Collection.objects.bulk_update(ordered, ["order"])
        Collection.objects.rebuild()
    return collection


def list_collection_segments(user, collection, params):
    children = list(collection.get_children())
    descendant_ids = list(collection.get_descendants().values_list("pk", flat=True))
    item_qs = CollectionItem.objects.filter(
        collection_id__in=[collection.pk, *descendant_ids]
    ).select_related("collection")
    items_by_collection = {}
    for item in item_qs:
        items_by_collection.setdefault(item.collection_id, {})[work_key(item)] = item

    user_works = load_filtered_user_works(user, params)
    uw_by_key = {work_key(user_work): user_work for user_work in user_works}

    def segment_works(item_map, nested=False):
        pairs = []
        for key, item in item_map.items():
            user_work = uw_by_key.get(key)
            if user_work is not None:
                pairs.append((user_work, item))
        if (params.get("sort") or "custom") == "custom":
            sort_asc = params.get("sort_asc", True)
            if nested:
                pairs.sort(
                    key=lambda pair: (pair[1].collection.lft, pair[1].order),
                    reverse=not sort_asc,
                )
            else:
                pairs.sort(key=lambda pair: pair[1].order, reverse=not sort_asc)
            return [user_work for user_work, _item in pairs]
        works = [user_work for user_work, _item in pairs]
        return sort_user_works(works, params)

    direct_map = items_by_collection.get(collection.pk, {})
    nested = []
    for child in children:
        child_ids = [child.pk, *child.get_descendants().values_list("pk", flat=True)]
        child_map = {}
        for child_id in child_ids:
            child_map.update(items_by_collection.get(child_id, {}))
        works = segment_works(child_map, nested=True)
        if works:
            nested.append({"collection": child, "user_works": works})
    return {
        "direct": segment_works(direct_map, nested=False),
        "nested": nested,
    }


def add_user_work_to_collection(user, collection, user_work):
    if user_work.user_id != user.id or collection.user_id != user.id:
        raise ValidationError("Нельзя изменить чужую коллекцию.")
    defaults = {"order": next_collection_item_order(collection)}
    try:
        with transaction.atomic():
            item, created = CollectionItem.objects.get_or_create(
                collection=collection,
                work_content_type=user_work.work_content_type,
                work_object_id=user_work.work_object_id,
                defaults=defaults,
            )
    except IntegrityError:
        item = CollectionItem.objects.get(
            collection=collection,
            work_content_type=user_work.work_content_type,
            work_object_id=user_work.work_object_id,
        )
        return item, False
    return item, created


def remove_user_work_from_collection(user, collection, user_work):
    if user_work.user_id != user.id or collection.user_id != user.id:
        raise ValidationError("Нельзя изменить чужую коллекцию.")
    deleted, _unused = CollectionItem.objects.filter(
        collection=collection,
        work_content_type=user_work.work_content_type,
        work_object_id=user_work.work_object_id,
    ).delete()
    return deleted > 0


def user_work_collection_ids(user, user_work):
    return set(
        CollectionItem.objects.filter(
            collection__user=user,
            work_content_type=user_work.work_content_type,
            work_object_id=user_work.work_object_id,
        ).values_list("collection_id", flat=True)
    )


def collection_tree_payload(user, member_ids=None):
    member_ids = set(member_ids or [])

    def walk(node):
        return {
            "id": node.pk,
            "name": node.name,
            "in_collection": node.pk in member_ids,
            "children": [walk(child) for child in node.get_children()],
        }

    return [walk(node) for node in get_user_collection_trees(user)]


def reorder_collection_items(user, collection, uw_ids):
    if collection.user_id != user.id:
        raise ValidationError("Нельзя изменить чужую коллекцию.")
    existing = {
        user_work.pk: user_work
        for user_work in UserWork.objects.filter(user=user, pk__in=uw_ids)
    }
    keys = []
    for uw_id in uw_ids:
        user_work = existing.get(uw_id)
        if user_work is not None:
            keys.append(work_key(user_work))
    items = {
        work_key(item): item
        for item in CollectionItem.objects.filter(collection=collection)
    }
    ordered = [items[key] for key in keys if key in items]
    to_update = []
    for index, item in enumerate(ordered):
        if item.order != index:
            item.order = index
            to_update.append(item)
    if to_update:
        CollectionItem.objects.bulk_update(to_update, ["order"])
    return len(ordered)
