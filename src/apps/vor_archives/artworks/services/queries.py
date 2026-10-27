from apps.vor_archives.registry import WORK_MODELS, WORK_TYPE_ICONS
from .content_types import ct_for_type
from ...prefetch import prefetch_user_works, prefetch_work_relations
from .utils import relation_cover_url, is_partial, item_ids
from apps.vor_archives.constants import STATUS_SORT_ORDER, UserWorkStatusChoices
from apps.vor_archives.models import UserWork


def sort_user_works(items, params, order_key=None):
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
    elif order_key is not None:
        items.sort(key=order_key, reverse=not sort_asc)
    else:
        items.sort(
            key=lambda uw: (uw.order_position, uw.date_added),
            reverse=not sort_asc,
        )
    return items


def load_filtered_user_works(user, params):
    types = [key for key in (params.get("types") or []) if key in WORK_MODELS]
    if not types:
        return []

    qs = UserWork.objects.filter(user=user).select_related("work_content_type")
    content_types = [ct_for_type(key) for key in types]
    qs = qs.filter(work_content_type__in=content_types)

    statuses = params.get("statuses")
    if is_partial(
        statuses, params.get("all_statuses") or list(UserWorkStatusChoices.values)
    ):
        qs = qs.filter(status__in=statuses or [])

    if not params.get("show_hidden", True):
        qs = qs.filter(is_hidden=False)

    items = list(qs)
    prefetch_user_works(items)
    prefetch_work_relations([uw.work for uw in items if uw.work], with_authors=False)
    return [
        user_work for user_work in items if _work_matches_filters(user_work, params)
    ]


def search_works(query, exclude_type=None, exclude_id=None, limit=20):
    exclude_id = int(exclude_id) if exclude_id not in (None, "") else None
    results = [
        _format_work_hit(type_key, work)
        for type_key, work in _iter_work_matches(
            query, limit, exclude_type=exclude_type, exclude_id=exclude_id
        )
    ]
    results.sort(key=lambda item: item["title"].casefold())
    return results[:limit]


def search_library_works(user, query, limit=15):
    query = (query or "").strip()
    if len(query) < 1:
        return {"owned": [], "other": []}

    owned_map = {}
    for user_work in UserWork.objects.filter(user=user).select_related(
        "work_content_type"
    ):
        owned_map[(user_work.work_content_type.model, user_work.work_object_id)] = (
            user_work.pk
        )

    owned = []
    other = []
    for type_key, work in _iter_work_matches(query, limit * 2):
        item = _format_work_hit(type_key, work)
        uw_id = owned_map.get((type_key, work.pk))
        if uw_id:
            item["uw_id"] = uw_id
            owned.append(item)
        else:
            other.append(item)
    owned.sort(key=lambda item: item["title"].casefold())
    other.sort(key=lambda item: item["title"].casefold())
    return {"owned": owned[:limit], "other": other[:limit]}


def _work_matches_filters(user_work, params):
    work = user_work.work
    if work is None:
        return False
    type_key = work._meta.model_name

    if is_partial(params.get("age_ratings"), params.get("all_age_ratings")):
        if work.age_rating not in (params.get("age_ratings") or []):
            return False

    if is_partial(params.get("tags"), params.get("all_tags")):
        work_tags = item_ids(work.tags.all())
        if not work_tags.intersection(params.get("tags") or []):
            return False

    genre_selected = params.get(f"genre_{type_key}")
    genre_all = params.get(f"all_genre_{type_key}")
    if is_partial(genre_selected, genre_all):
        work_genres = item_ids(work.genres.all())
        if not work_genres.intersection(genre_selected or []):
            return False

    if type_key == "game" and is_partial(
        params.get("platforms"), params.get("all_platforms")
    ):
        work_platforms = item_ids(work.platforms.all())
        if not work_platforms.intersection(params.get("platforms") or []):
            return False
    return True


def _iter_work_matches(query, limit, exclude_type=None, exclude_id=None):
    """Yield (type_key, work) for every work matching the query."""
    query = (query or "").strip()
    if len(query) < 1:
        return
    for type_key, model in WORK_MODELS.items():
        qs = model.objects.filter(title__icontains=query)
        if type_key == exclude_type and exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        for work in qs.order_by("title")[:limit]:
            yield type_key, work


def _format_work_hit(type_key, work):
    return {
        "type_key": type_key,
        "work_id": work.pk,
        "title": work.title,
        "cover_url": relation_cover_url(work),
        "icon": WORK_TYPE_ICONS.get(type_key, "bi bi-collection"),
    }
