"""Context builders for the artworks overlay."""

from django.urls import reverse

from apps.vor_archives.constants import (
    AgeRatingChoices,
    RELATION_TYPE_OPTIONS,
    age_rating_options,
    status_choices,
    status_options,
)
from .services.catalog import attr_catalog, chip_payload
from .services.progress import get_progress_info, work_progress
from .services.works import work_relation_items, work_type_key


def build_overlay_context(
    request,
    work,
    user_work=None,
    work_form=None,
    user_work_form=None,
    editing=False,
    global_edit=False,
):
    type_key = work_type_key(work)
    owned = user_work is not None
    if owned:
        progress_meta = get_progress_info(user_work) or {}
    else:
        work_meta = work_progress(work)
        progress_meta = {
            "value": 0,
            "maximum": work_meta.maximum,
            "unit": work_meta.unit,
            "step": work_meta.step,
        }
    owned_platform_ids = []
    if owned:
        owned_platform_ids = list(
            user_work.owned_platforms.values_list("pk", flat=True)
        )
    catalog = attr_catalog(type_key)
    save_url = (
        reverse("vor_archives:artworks:detail", args=[user_work.pk])
        if owned
        else reverse("vor_archives:artworks:work", args=[type_key, work.pk])
    )
    return {
        "user_work": user_work,
        "owned": owned,
        "work": work,
        "work_type": type_key,
        "work_form": work_form,
        "user_work_form": user_work_form,
        "is_staff": request.user.is_staff,
        "editing": editing,
        "global_edit": global_edit,
        "progress_unit": progress_meta.get("unit", ""),
        "progress_meta": progress_meta,
        "hide_platforms": type_key != "game" or not owned,
        "owned_platform_ids": owned_platform_ids,
        "status_choices": status_choices(),
        "age_rating_choices": AgeRatingChoices.choices,
        "work_relations": work_relation_items(work),
        "overlay_opts": {
            "editing": editing,
            "globalEdit": global_edit,
            "owned": owned,
            "isStaff": request.user.is_staff,
            "workType": type_key,
            "workId": work.pk,
            "filmType": getattr(work, "film_type", None) or "movie",
            "status": user_work.status if owned else "planning",
            "statusChoices": status_options(),
            "attachUrl": reverse("vor_archives:artworks:attach"),
            "rating": (user_work.rating or 0) if owned else 0,
            "isHidden": user_work.is_hidden if owned else False,
            "progress": progress_meta.get("value", 0),
            "progressMax": progress_meta.get("maximum"),
            "progressUnit": progress_meta.get("unit", ""),
            "progressStep": progress_meta.get("step", 1),
            "timesCompleted": user_work.times_completed if owned else 0,
            "lastCompletedDate": (
                user_work.last_completed_date.strftime("%d.%m.%Y")
                if owned and user_work.last_completed_date
                else ""
            ),
            "quickUrl": (
                reverse("vor_archives:artworks:quick", args=[user_work.pk])
                if owned
                else ""
            ),
            "listUrl": reverse("vor_archives:artworks:list"),
            "saveUrl": save_url,
            "relationSearchUrl": reverse("vor_archives:artworks:relation_search"),
            "title": work.title,
            "description": work.description or "",
            "releaseDate": work.release_date.isoformat() if work.release_date else "",
            "ageRating": work.age_rating or "",
            "externalLink": work.external_link or "",
            "pages": getattr(work, "pages", None),
            "durationMinutes": getattr(work, "duration_minutes", None),
            "episodeCount": getattr(work, "episode_count", None),
            "coverUrl": work.cover.url if work.cover else "",
            "authors": chip_payload(work.authors.all(), "bio"),
            "genres": chip_payload(work.genres.all()),
            "tags": chip_payload(work.tags.all()),
            "platforms": chip_payload(work.platforms.all(), "")
            if type_key == "game"
            else [],
            "ownedPlatformIds": owned_platform_ids,
            "catalog": catalog,
            "relations": work_relation_items(work),
            "relationTypes": RELATION_TYPE_OPTIONS,
            "ageChoices": age_rating_options(),
        },
    }
