from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Max, Q, prefetch_related_objects
from django.shortcuts import get_object_or_404

from .constants import FilmTypeChoices, UserWorkStatusChoices, WorkRelationTypeChoices
from .models import Book, FeedItem, Film, Game, UserWork, WorkRelation

WORK_MODELS = {
    "book": Book,
    "film": Film,
    "game": Game,
}


def get_work_model(type_key: str):
    try:
        return WORK_MODELS[type_key]
    except KeyError:
        raise ValueError(f"Unknown work type: {type_key}")


def get_work(type_key: str, work_id: int):
    return get_object_or_404(get_work_model(type_key), pk=work_id)


def work_type_key(work) -> str:
    return work._meta.model_name


def get_user_work(user, work):
    ct = ContentType.objects.get_for_model(work)
    return UserWork.objects.filter(
        user=user,
        work_content_type=ct,
        work_object_id=work.pk,
    ).first()


def user_has_work(user, work) -> bool:
    return get_user_work(user, work) is not None


def user_owned_work_ids(user, type_key):
    model = get_work_model(type_key)
    ct = ContentType.objects.get_for_model(model)
    return UserWork.objects.filter(
        user=user,
        work_content_type=ct,
    ).values_list("work_object_id", flat=True)


def user_has_work_title(user, type_key, title) -> bool:
    title = (title or "").strip()
    if not title:
        return False
    model = get_work_model(type_key)
    owned_ids = user_owned_work_ids(user, type_key)
    return model.objects.filter(pk__in=owned_ids, title__iexact=title).exists()


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
    qs = UserWork.objects.filter(user=user, pk__in=ids).select_related("work_content_type")
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


def next_order_position(user):
    current = UserWork.objects.filter(user=user).aggregate(m=Max("order_position"))["m"]
    return 0 if current is None else current + 1


def attach_work(user, type_key, work_id, cleaned_user_data=None):
    work = get_work(type_key, work_id)
    ct = ContentType.objects.get_for_model(work)
    defaults = {}
    m2m_platforms = None
    if cleaned_user_data:
        for key, value in cleaned_user_data.items():
            if key == "owned_platforms":
                m2m_platforms = value
            else:
                defaults[key] = value
    if "order_position" not in defaults:
        defaults["order_position"] = next_order_position(user)

    user_work, created = UserWork.objects.get_or_create(
        user=user,
        work_content_type=ct,
        work_object_id=work.pk,
        defaults=defaults,
    )
    if created and m2m_platforms is not None:
        user_work.owned_platforms.set(m2m_platforms)
    return user_work, created


WORK_TYPE_ICONS = {
    "book": "icon-book-text",
    "film": "icon-clapperboard",
    "game": "icon-gamepad-2",
}

RELATION_LABELS = {
    WorkRelationTypeChoices.SEQUEL: ("Продолжение", "Предыстория"),
    WorkRelationTypeChoices.SPIN_OFF: ("Спин-офф", "Оригинал"),
    WorkRelationTypeChoices.ADAPTATION: ("Адаптация", "Первоисточник"),
    WorkRelationTypeChoices.REMAKE: ("Ремейк", "Оригинал"),
    WorkRelationTypeChoices.OTHER: ("Связано", "Связано"),
}


def _relation_cover_url(work):
    cover = getattr(work, "cover", None)
    if not cover:
        return ""
    try:
        return cover.url
    except ValueError:
        return ""


def relation_label(relation_type, direction="out"):
    outgoing_label, incoming_label = RELATION_LABELS.get(
        relation_type, ("Связано", "Связано")
    )
    return outgoing_label if direction == "out" else incoming_label


def _relation_item(work, label, relation, direction):
    return {
        "id": relation.pk,
        "title": work.title,
        "cover_url": _relation_cover_url(work),
        "label": label,
        "icon": WORK_TYPE_ICONS.get(work._meta.model_name, "bi bi-collection"),
        "type_key": work._meta.model_name,
        "work_id": work.pk,
        "relation_type": relation.relation_type,
        "direction": direction,
    }


def work_relation_items(work):
    """Связанные произведения с подписью относительно текущего."""
    ct = ContentType.objects.get_for_model(work)
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
            _relation_item(other, relation_label(relation.relation_type, "out"), relation, "out")
        )
    for relation in incoming:
        other = relation.source
        if other is None:
            continue
        items.append(
            _relation_item(other, relation_label(relation.relation_type, "in"), relation, "in")
        )
    return items


def search_works(query, exclude_type=None, exclude_id=None, limit=20):
    query = (query or "").strip()
    if len(query) < 1:
        return []
    results = []
    exclude_id = int(exclude_id) if exclude_id not in (None, "") else None
    for type_key, model in WORK_MODELS.items():
        qs = model.objects.filter(title__icontains=query)
        if type_key == exclude_type and exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        for work in qs.order_by("title")[:limit]:
            results.append({
                "type_key": type_key,
                "work_id": work.pk,
                "title": work.title,
                "cover_url": _relation_cover_url(work),
                "icon": WORK_TYPE_ICONS.get(type_key, "bi bi-collection"),
            })
    results.sort(key=lambda item: item["title"].casefold())
    return results[:limit]


def _work_progress_maximum(work):
    model_name = work._meta.model_name
    if model_name == "book":
        return work.pages
    if model_name == "film":
        if work.film_type == FilmTypeChoices.TV_SHOW:
            return work.episode_count
        return work.duration_minutes
    return None


def clamp_progress_for_work(work):
    maximum = _work_progress_maximum(work)
    if maximum is None:
        return
    limit = Decimal(str(maximum))
    user_works = list(work.user_works.all())
    for user_work in user_works:
        if user_work.progress > limit:
            user_work.progress = limit
            user_work.save()


@transaction.atomic
def sync_work_relations(work, items):
    ct = ContentType.objects.get_for_model(work)
    keep_ids = []
    new_items = []
    for item in items:
        relation_id = item.get("id")
        relation_type = item.get("relation_type") or WorkRelationTypeChoices.OTHER
        if relation_id:
            relation = WorkRelation.objects.filter(pk=relation_id).first()
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
        relation = WorkRelation(
            source_content_type=ct,
            source_object_id=work.pk,
            target_content_type=ContentType.objects.get_for_model(target),
            target_object_id=target.pk,
            relation_type=relation_type,
        )
        relation.save()


def create_work_and_attach(user, work, user_work_form):
    user_work = user_work_form.save(commit=False)
    user_work.user = user
    user_work.work = work
    user_work.order_position = next_order_position(user)
    user_work.save()
    user_work_form.save_m2m()
    return user_work


STATUS_SORT_ORDER = {
    UserWorkStatusChoices.PLANNING: 0,
    UserWorkStatusChoices.IN_PROGRESS: 1,
    UserWorkStatusChoices.COMPLETED: 2,
    UserWorkStatusChoices.DROPPED: 3,
}


def _as_str_set(values):
    return {str(value) for value in (values or [])}


def _is_partial(selected, all_values):
    if not all_values:
        return False
    return _as_str_set(selected) != _as_str_set(all_values)


def _item_ids(items):
    return {item.pk for item in items}


def _prefetch_work_filters(user_works):
    prefetch_related_objects(user_works, "work")
    by_type = {"book": [], "film": [], "game": []}
    for user_work in user_works:
        work = user_work.work
        if work is None:
            continue
        by_type.get(work._meta.model_name, []).append(work)
    for type_key, works in by_type.items():
        if not works:
            continue
        related = ["tags", "genres"]
        if type_key == "game":
            related.append("platforms")
        prefetch_related_objects(works, *related)


def _work_matches_filters(user_work, params):
    work = user_work.work
    if work is None:
        return False
    type_key = work._meta.model_name

    if _is_partial(params.get("age_ratings"), params.get("all_age_ratings")):
        if work.age_rating not in (params.get("age_ratings") or []):
            return False

    if _is_partial(params.get("tags"), params.get("all_tags")):
        work_tags = _item_ids(work.tags.all())
        if not work_tags.intersection(params.get("tags") or []):
            return False

    genre_selected = params.get(f"genre_{type_key}")
    genre_all = params.get(f"all_genre_{type_key}")
    if _is_partial(genre_selected, genre_all):
        work_genres = _item_ids(work.genres.all())
        if not work_genres.intersection(genre_selected or []):
            return False

    if type_key == "game" and _is_partial(params.get("platforms"), params.get("all_platforms")):
        work_platforms = _item_ids(work.platforms.all())
        if not work_platforms.intersection(params.get("platforms") or []):
            return False
    return True


def list_user_works(user, params):
    types = [key for key in (params.get("types") or []) if key in WORK_MODELS]
    if not types:
        return []

    qs = UserWork.objects.filter(user=user).select_related("work_content_type")
    content_types = [
        ContentType.objects.get_for_model(WORK_MODELS[key]) for key in types
    ]
    qs = qs.filter(work_content_type__in=content_types)

    statuses = params.get("statuses")
    if _is_partial(statuses, params.get("all_statuses") or list(UserWorkStatusChoices.values)):
        qs = qs.filter(status__in=statuses or [])

    if not params.get("show_hidden", True):
        qs = qs.filter(is_hidden=False)

    items = list(qs)
    _prefetch_work_filters(items)
    items = [user_work for user_work in items if _work_matches_filters(user_work, params)]

    sort_field = params.get("sort") or "custom"
    sort_asc = params.get("sort_asc", True)

    if sort_field == "rating":
        items.sort(
            key=lambda uw: (
                uw.rating is None,
                -(uw.rating or 0) if not sort_asc else (uw.rating or 0),
            )
        )
    elif sort_field == "title":
        items.sort(
            key=lambda uw: (uw.work.title if uw.work else "").casefold(),
            reverse=not sort_asc,
        )
    elif sort_field == "status":
        items.sort(
            key=lambda uw: STATUS_SORT_ORDER.get(uw.status, 99),
            reverse=not sort_asc,
        )
    elif sort_field == "date_added":
        items.sort(key=lambda uw: uw.date_added, reverse=not sort_asc)
    else:
        items.sort(
            key=lambda uw: (uw.order_position, uw.date_added),
            reverse=not sort_asc,
        )
    return items


def reorder_user_works(user, ids):
    existing = {
        user_work.pk: user_work
        for user_work in UserWork.objects.filter(user=user, pk__in=ids)
    }
    ordered = [existing[uw_id] for uw_id in ids if uw_id in existing]
    positions = sorted(user_work.order_position for user_work in ordered)
    to_update = []
    for position, user_work in zip(positions, ordered):
        if user_work.order_position != position:
            user_work.order_position = position
            to_update.append(user_work)
    if to_update:
        UserWork.objects.bulk_update(to_update, ["order_position"])
    return len(ordered)


def search_library_works(user, query, limit=15):
    query = (query or "").strip()
    if len(query) < 1:
        return {"owned": [], "other": []}

    owned_map = {}
    for user_work in UserWork.objects.filter(user=user).select_related("work_content_type"):
        owned_map[(user_work.work_content_type.model, user_work.work_object_id)] = user_work.pk

    owned = []
    other = []
    for type_key, model in WORK_MODELS.items():
        for work in model.objects.filter(title__icontains=query).order_by("title")[: limit * 2]:
            item = {
                "type_key": type_key,
                "work_id": work.pk,
                "title": work.title,
                "cover_url": _relation_cover_url(work),
                "icon": WORK_TYPE_ICONS.get(type_key, "bi bi-collection"),
            }
            uw_id = owned_map.get((type_key, work.pk))
            if uw_id:
                item["uw_id"] = uw_id
                owned.append(item)
            else:
                other.append(item)
    owned.sort(key=lambda item: item["title"].casefold())
    other.sort(key=lambda item: item["title"].casefold())
    return {"owned": owned[:limit], "other": other[:limit]}
