from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.vor_archives.constants import (
    AgeRatingChoices,
    UserWorkStatusChoices,
    STATUS_LABELS_RU,
    LOGIN_URL,
)
from apps.vor_archives.models import (
    UserWork,
)
from ..services import (
    WORK_MODELS,
    delete_user_works,
    get_user_collection,
    get_user_work,
    get_work,
    list_collection_segments,
    list_user_works,
    sync_work_relations,
)

from .utils import (
    parse_ids,
    artwork_list_params,
    artwork_overlay_response,
    get_work_form_class,
    parse_id_list,
    parse_relations_payload,
    progress_meta_for_work,
    all_attr_catalogs,
    list_response,
)
from .constants import RELATION_TYPE_OPTIONS


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_list(request):
    params = artwork_list_params(request)
    collection = None
    direct = []
    nested = []
    if params.get("collection_id"):
        collection = get_user_collection(request.user, params["collection_id"])
        segments = list_collection_segments(request.user, collection, params)
        direct = segments["direct"]
        nested = segments["nested"]
        user_works = []
    else:
        user_works = list_user_works(request.user, params)
    return render(
        request,
        "vor_archives/partials/artwork_list.html",
        {
            "collection": collection,
            "user_works": user_works,
            "direct": direct,
            "nested": nested,
            "has_collection_items": bool(direct or nested),
        },
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_add(request):
    if request.method == "POST":
        type_key = request.POST.get("work_type", "book")
        work_form_class = get_work_form_class(type_key)
        if work_form_class is None:
            return HttpResponseBadRequest("Неизвестный тип")
        post = request.POST.copy()
        for name in ("authors", "tags", "genres", "platforms"):
            ids = parse_id_list(request, name)
            post.setlist(name, [str(item) for item in ids])
        work_form = work_form_class(post, request.FILES)
        if work_form.is_valid():
            try:
                with transaction.atomic():
                    work = work_form.save()
                    sync_work_relations(work, parse_relations_payload(request))
            except ValidationError as error:
                message = (
                    " ".join(error.messages)
                    if getattr(error, "messages", None)
                    else str(error)
                )
                return JsonResponse(
                    {"ok": False, "errors": {"__all__": [{"message": message}]}},
                    status=400,
                )
            meta = progress_meta_for_work(work)
            return JsonResponse(
                {
                    "ok": True,
                    "work_id": work.pk,
                    "work_type": type_key,
                    "title": work.title,
                    "progressMax": meta["maximum"],
                    "progressUnit": meta["unit"],
                    "progressStep": meta["step"],
                }
            )
        return JsonResponse(
            {"ok": False, "errors": work_form.errors.get_json_data()},
            status=400,
        )

    return render(
        request,
        "vor_archives/partials/artwork_add.html",
        {
            "add_opts": {
                "workType": "book",
                "saveUrl": reverse("vor_archives:artworks:add"),
                "searchUrl": reverse("vor_archives:artworks:search"),
                "previewUrl": reverse("vor_archives:artworks:preview"),
                "attachUrl": reverse("vor_archives:artworks:attach"),
                "listUrl": reverse("vor_archives:artworks:list"),
                "relationSearchUrl": reverse("vor_archives:artworks:relation_search"),
                "relationTypes": RELATION_TYPE_OPTIONS,
                "catalogs": all_attr_catalogs(),
                "ageChoices": [
                    {"value": value, "label": label}
                    for value, label in AgeRatingChoices.choices
                ],
                "statusChoices": [
                    {"value": value, "label": STATUS_LABELS_RU.get(value, label)}
                    for value, label in UserWorkStatusChoices.choices
                ],
            },
        },
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_detail(request, uw_id):
    user_work = get_object_or_404(UserWork, pk=uw_id, user=request.user)
    work = user_work.work
    if work is None:
        return HttpResponseBadRequest("Произведение не найдено")
    return artwork_overlay_response(request, work, user_work)


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_work(request, type_key, work_id):
    if type_key not in WORK_MODELS:
        return HttpResponseBadRequest("Неизвестный тип")
    work = get_work(type_key, work_id)
    user_work = get_user_work(request.user, work)
    return artwork_overlay_response(request, work, user_work)


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_delete(request):
    ids = parse_ids(request)
    delete_user_works(request.user, ids)
    return list_response(request, '{"vor:close-overlay": true}')
