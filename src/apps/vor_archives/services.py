from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Q, prefetch_related_objects
from django.shortcuts import get_object_or_404

from .constants import WorkRelationTypeChoices
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


def _relation_item(work, label):
    return {
        "title": work.title,
        "cover_url": _relation_cover_url(work),
        "label": label,
        "icon": WORK_TYPE_ICONS.get(work._meta.model_name, "bi bi-collection"),
        "type_key": work._meta.model_name,
        "work_id": work.pk,
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
        outgoing_label, _incoming_label = RELATION_LABELS.get(
            relation.relation_type, ("Связано", "Связано")
        )
        items.append(_relation_item(other, outgoing_label))
    for relation in incoming:
        other = relation.source
        if other is None:
            continue
        _outgoing_label, incoming_label = RELATION_LABELS.get(
            relation.relation_type, ("Связано", "Связано")
        )
        items.append(_relation_item(other, incoming_label))
    return items


def create_work_and_attach(user, work, user_work_form):
    user_work = user_work_form.save(commit=False)
    user_work.user = user
    user_work.work = work
    user_work.save()
    user_work_form.save_m2m()
    return user_work
