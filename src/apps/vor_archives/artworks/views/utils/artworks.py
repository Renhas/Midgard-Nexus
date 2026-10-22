import json

from django.core.exceptions import ValidationError
from django.db.models import prefetch_related_objects
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import render
from django.urls import reverse

from apps.vor_archives.constants import (
    AgeRatingChoices,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
    STATUS_LABELS_RU,
)
from apps.vor_archives.artworks.forms import WORK_FORMS, UserWorkEditForm
from apps.vor_archives.models import (
    BookGenre,
    FilmGenre,
    GameGenre,
    Person,
    Platform,
    Tag,
)
from apps.vor_archives.artworks.services import (
    WORK_MODELS,
    clamp_progress_for_work,
    get_progress_info,
    sync_work_relations,
    unit_for_type,
    work_progress,
    work_relation_items,
    work_type_key,
)

from .common import optional_int
from ..constants import RELATION_TYPE_OPTIONS


def all_attr_catalogs():
    return {key: _attr_catalog(key) for key in WORK_FORMS}


def progress_meta_for_work(work):
    meta = work_progress(work)
    return {"maximum": meta.maximum, "unit": meta.unit, "step": meta.step}


def wants_json(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def parse_id_list(request, name):
    values = []
    for raw in request.POST.getlist(name):
        for part in str(raw).split(","):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(int(part))
            except ValueError:
                continue
    return values


def parse_relations_payload(request):
    raw = request.POST.get("relations_json") or "[]"
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    parsed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        entry = {
            "id": item.get("id") or None,
            "relation_type": item.get("relation_type") or WorkRelationTypeChoices.OTHER,
            "type_key": item.get("type_key"),
            "work_id": item.get("work_id"),
        }
        if entry["id"]:
            try:
                entry["id"] = int(entry["id"])
            except (TypeError, ValueError):
                entry["id"] = None
        if entry["work_id"]:
            try:
                entry["work_id"] = int(entry["work_id"])
            except (TypeError, ValueError):
                entry["work_id"] = None
        parsed.append(entry)
    return parsed


def artwork_list_params(request):
    types = [key for key in request.GET.getlist("types") if key in WORK_MODELS]
    if "types" not in request.GET:
        types = list(WORK_MODELS.keys())
    return {
        "types": types,
        "statuses": [value for value in request.GET.getlist("status") if value],
        "age_ratings": [value for value in request.GET.getlist("age_rating") if value],
        "tags": _id_list(request, "tags"),
        "genre_book": _id_list(request, "genre_book"),
        "genre_film": _id_list(request, "genre_film"),
        "genre_game": _id_list(request, "genre_game"),
        "platforms": _id_list(request, "platform"),
        "all_statuses": list(UserWorkStatusChoices.values),
        "all_age_ratings": list(AgeRatingChoices.values),
        "all_tags": list(Tag.objects.values_list("pk", flat=True)),
        "all_genre_book": list(BookGenre.objects.values_list("pk", flat=True)),
        "all_genre_film": list(FilmGenre.objects.values_list("pk", flat=True)),
        "all_genre_game": list(GameGenre.objects.values_list("pk", flat=True)),
        "all_platforms": list(Platform.objects.values_list("pk", flat=True)),
        "sort": request.GET.get("sort") or "custom",
        "sort_asc": request.GET.get("dir", "asc") != "desc",
        "show_hidden": request.GET.get("hidden", "1") != "0",
        "collection_id": optional_int(request.GET.get("collection")),
    }


def list_response(request, trigger=None):
    payload = {"vor:reload-list": True}
    if trigger:
        extra = json.loads(trigger) if isinstance(trigger, str) else dict(trigger)
        payload.update(extra)
    response = HttpResponse()
    response["HX-Trigger"] = json.dumps(payload)
    return response


def get_work_form_class(type_key):
    try:
        return WORK_FORMS[type_key]
    except KeyError:
        return None


def artwork_overlay_response(request, work, user_work=None):
    type_key = _prefetch_work(work, user_work)
    work_form_class = get_work_form_class(type_key)

    if request.method == "POST":
        if not request.user.is_staff:
            return HttpResponseBadRequest("Недостаточно прав")
        post = request.POST.copy()
        for name in ("authors", "tags", "genres", "platforms"):
            ids = parse_id_list(request, name)
            post.setlist(name, [str(item) for item in ids])
        work_form = work_form_class(post, request.FILES, instance=work)
        if work_form.is_valid():
            saved = work_form.save()
            if post.get("cover_clear") == "1" and not request.FILES.get("cover"):
                if saved.cover:
                    saved.cover.delete(save=False)
                saved.cover = None
                saved.save(update_fields=["cover"])
            try:
                sync_work_relations(saved, parse_relations_payload(request))
            except ValidationError as error:
                work_form.add_error(None, error)
            else:
                clamp_progress_for_work(saved)
                if type_key == "game" and user_work is not None:
                    valid_ids = set(saved.platforms.values_list("pk", flat=True))
                    stale_ids = [
                        pk
                        for pk in user_work.owned_platforms.values_list("pk", flat=True)
                        if pk not in valid_ids
                    ]
                    if stale_ids:
                        user_work.owned_platforms.remove(*stale_ids)
                _prefetch_work(saved, user_work)
                response = render(
                    request,
                    "vor_archives/partials/artwork_overlay.html",
                    _detail_context(
                        request,
                        saved,
                        user_work,
                        work_form_class(instance=saved),
                        UserWorkEditForm(instance=user_work)
                        if user_work is not None
                        else None,
                    ),
                )
                response["HX-Trigger"] = json.dumps({"vor:reload-list": True})
                return response
        return render(
            request,
            "vor_archives/partials/artwork_overlay.html",
            _detail_context(
                request,
                work,
                user_work,
                work_form,
                UserWorkEditForm(instance=user_work) if user_work is not None else None,
                editing=True,
                global_edit=True,
            ),
        )

    start_editing = (
        request.method == "GET"
        and request.GET.get("edit") == "1"
        and request.user.is_staff
    )
    return render(
        request,
        "vor_archives/partials/artwork_overlay.html",
        _detail_context(
            request,
            work,
            user_work,
            work_form_class(instance=work),
            UserWorkEditForm(instance=user_work) if user_work is not None else None,
            editing=start_editing,
            global_edit=start_editing,
        ),
    )


def _chip_payload(items, tip_field="description"):
    payload = []
    for item in items:
        payload.append(
            {
                "id": item.pk,
                "name": item.name,
                "tip": getattr(item, tip_field, "") or "",
            }
        )
    return payload


def _attr_catalog(type_key):
    genre_model = {"book": BookGenre, "film": FilmGenre, "game": GameGenre}[type_key]
    return {
        "authors": _chip_payload(Person.objects.order_by("name"), "bio"),
        "genres": _chip_payload(genre_model.objects.order_by("name")),
        "tags": _chip_payload(Tag.objects.order_by("name")),
        "platforms": _chip_payload(Platform.objects.order_by("name"), "")
        if type_key == "game"
        else [],
    }


def _prefetch_work(work, user_work=None):
    type_key = work_type_key(work)
    related = ["authors", "tags", "genres"]
    if type_key == "game":
        related.append("platforms")
    prefetch_related_objects([work], *related)
    if user_work is not None:
        prefetch_related_objects([user_work], "owned_platforms")
    return type_key


def _progress_unit(work=None, type_key=None, film_type=None):
    if work is not None:
        return work_progress(work).unit
    return unit_for_type(type_key, film_type=film_type)


def _id_list(request, name):
    values = []
    for raw in request.GET.getlist(name):
        try:
            values.append(int(raw))
        except (TypeError, ValueError):
            continue
    return values


def _detail_context(
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
        work_meta = progress_meta_for_work(work)
        progress_meta = {
            "value": 0,
            "maximum": work_meta["maximum"],
            "unit": work_meta["unit"],
            "step": work_meta["step"],
        }
    owned_platform_ids = []
    if owned:
        owned_platform_ids = list(
            user_work.owned_platforms.values_list("pk", flat=True)
        )
    catalog = _attr_catalog(type_key)
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
        "progress_unit": _progress_unit(work),
        "progress_meta": progress_meta,
        "hide_platforms": type_key != "game" or not owned,
        "owned_platform_ids": owned_platform_ids,
        "status_choices": [
            (value, STATUS_LABELS_RU.get(value, label))
            for value, label in UserWorkStatusChoices.choices
        ],
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
            "statusChoices": [
                {"value": value, "label": STATUS_LABELS_RU.get(value, label)}
                for value, label in UserWorkStatusChoices.choices
            ],
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
            "authors": _chip_payload(work.authors.all(), "bio"),
            "genres": _chip_payload(work.genres.all()),
            "tags": _chip_payload(work.tags.all()),
            "platforms": _chip_payload(work.platforms.all(), "")
            if type_key == "game"
            else [],
            "ownedPlatformIds": owned_platform_ids,
            "catalog": catalog,
            "relations": work_relation_items(work),
            "relationTypes": RELATION_TYPE_OPTIONS,
            "ageChoices": [
                {"value": value, "label": label}
                for value, label in AgeRatingChoices.choices
            ],
        },
    }
