import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.vor_archives.constants import (
    RELATION_TYPE_OPTIONS,
    age_rating_options,
    status_options,
)
from apps.vor_archives.registry import WORK_MODELS
from apps.vor_archives.models import UserWork
from apps.vor_archives.artworks.forms import RelationsForm, UserWorkEditForm
from apps.vor_archives.artworks.presenters import build_overlay_context
from apps.vor_archives.artworks.services import (
    delete_user_works,
    get_user_collection,
    get_user_work,
    get_work,
    list_collection_segments,
    list_user_works,
    list_user_works_in_collection,
    save_work_with_relations,
)
from apps.vor_archives.artworks.services.catalog import all_attr_catalogs
from apps.vor_archives.artworks.services.prefetch import prefetch_work_with_user_work

from .utils import (
    parse_ids,
    artwork_list_params,
    get_work_form_class,
    parse_id_list,
    progress_meta_for_work,
    list_response,
)


@login_required
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
        user_works = list_user_works_in_collection(request.user, params)
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


@login_required
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
        relations_form = RelationsForm(post)

        if work_form.is_valid() and relations_form.is_valid():
            try:
                work = save_work_with_relations(
                    work_form, relations_form.cleaned_data["relations_json"]
                )
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
                "ageChoices": age_rating_options(),
                "statusChoices": status_options(),
            },
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def artwork_detail(request, uw_id):
    user_work = get_object_or_404(UserWork, pk=uw_id, user=request.user)
    work = user_work.work
    if work is None:
        return HttpResponseBadRequest("Произведение не найдено")
    return artwork_overlay_response(request, work, user_work)


@login_required
@require_http_methods(["GET", "POST"])
def artwork_work(request, type_key, work_id):
    if type_key not in WORK_MODELS:
        return HttpResponseBadRequest("Неизвестный тип")
    work = get_work(type_key, work_id)
    user_work = get_user_work(request.user, work)
    return artwork_overlay_response(request, work, user_work)


@login_required
@require_POST
def artwork_delete(request):
    ids = parse_ids(request)
    delete_user_works(request.user, ids)
    return list_response(request, '{"vor:close-overlay": true}')


def artwork_overlay_response(request, work, user_work=None):
    type_key = prefetch_work_with_user_work(work, user_work)
    work_form_class = get_work_form_class(type_key)

    if request.method == "POST":
        if not request.user.is_staff:
            return HttpResponseBadRequest("Недостаточно прав")
        post = request.POST.copy()
        for name in ("authors", "tags", "genres", "platforms"):
            ids = parse_id_list(request, name)
            post.setlist(name, [str(item) for item in ids])

        work_form = work_form_class(post, request.FILES, instance=work)
        relations_form = RelationsForm(post)

        if work_form.is_valid() and relations_form.is_valid():
            try:
                saved = save_work_with_relations(
                    work_form,
                    relations_form.cleaned_data["relations_json"],
                    user_work,
                )
            except ValidationError as error:
                work_form.add_error(None, error)
            else:
                prefetch_work_with_user_work(saved, user_work)
                response = render(
                    request,
                    "vor_archives/partials/artwork_overlay.html",
                    build_overlay_context(
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
            build_overlay_context(
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
        build_overlay_context(
            request,
            work,
            user_work,
            work_form_class(instance=work),
            UserWorkEditForm(instance=user_work) if user_work is not None else None,
            editing=start_editing,
            global_edit=start_editing,
        ),
    )
