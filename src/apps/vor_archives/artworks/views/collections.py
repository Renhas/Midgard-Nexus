import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.vor_archives.models import UserWork
from ..services import (
    add_user_work_to_collection,
    collection_tree_payload,
    create_collection,
    delete_collection,
    get_user_collection,
    get_user_collection_trees,
    move_collection,
    remove_user_work_from_collection,
    rename_collection,
    reorder_collection_items,
    user_work_collection_ids,
)

from .utils import optional_int, parse_ids


@login_required
@require_GET
def artwork_collections(request, uw_id):
    user_work = get_object_or_404(UserWork, user=request.user, pk=uw_id)
    member_ids = user_work_collection_ids(request.user, user_work)
    return JsonResponse(
        {
            "tree": collection_tree_payload(request.user, member_ids),
        }
    )


@login_required
@require_GET
def collection_tree(request):
    return render(
        request,
        "vor_archives/partials/collection_tree.html",
        {
            "collections": get_user_collection_trees(request.user),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def collection_new(request):
    error = ""
    name = ""
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        try:
            create_collection(request.user, name)
            return _collection_mutation_response()
        except ValidationError as exc:
            error = (
                " ".join(exc.messages) if getattr(exc, "messages", None) else str(exc)
            )
    return _collection_form_response(
        request,
        "vor_archives/partials/collection_form.html",
        {
            "title": "Новая коллекция",
            "submit_label": "Создать",
            "action_url": reverse("vor_archives:collections:new"),
            "name": name,
            "error": error,
        },
    )


@login_required
@require_GET
def collection_edit(request, pk):
    collection = get_user_collection(request.user, pk)
    return render(
        request,
        "vor_archives/partials/collection_form.html",
        {
            "title": "Переименовать коллекцию",
            "submit_label": "Сохранить",
            "action_url": reverse(
                "vor_archives:collections:update", args=[collection.pk]
            ),
            "name": collection.name,
            "error": "",
        },
    )


@login_required
@require_POST
def collection_update(request, pk):
    name = (request.POST.get("name") or "").strip()
    try:
        rename_collection(request.user, pk, name)
        response = _collection_mutation_response()
        extra = json.loads(response["HX-Trigger"])
        extra["vor:collection-renamed"] = {"id": pk, "name": name}
        response["HX-Trigger"] = json.dumps(extra)
        return response
    except ValidationError as exc:
        error = " ".join(exc.messages) if getattr(exc, "messages", None) else str(exc)
        collection = get_user_collection(request.user, pk)
        return render(
            request,
            "vor_archives/partials/collection_form.html",
            {
                "title": "Переименовать коллекцию",
                "submit_label": "Сохранить",
                "action_url": reverse(
                    "vor_archives:collections:update", args=[collection.pk]
                ),
                "name": name,
                "error": error,
            },
        )


@login_required
@require_GET
def collection_delete_preview(request, pk):
    collection = get_user_collection(request.user, pk)
    child_count = collection.get_descendant_count()
    return render(
        request,
        "vor_archives/partials/collection_delete_confirm.html",
        {
            "collection": collection,
            "child_count": child_count,
        },
    )


@login_required
@require_POST
def collection_delete(request, pk):
    delete_collection(request.user, pk)
    response = _collection_mutation_response()
    extra = json.loads(response["HX-Trigger"])
    extra["vor:collection-deleted"] = pk
    response["HX-Trigger"] = json.dumps(extra)
    return response


@login_required
@require_POST
def collection_reorder(request):
    collection_id = optional_int(request.POST.get("id"))
    parent_id = optional_int(request.POST.get("parent_id"))
    if not collection_id:
        return HttpResponseBadRequest("Не указана коллекция")
    try:
        move_collection(
            request.user,
            collection_id,
            parent_id,
            request.POST.getlist("sibling_ids"),
        )
    except ValidationError as exc:
        message = " ".join(exc.messages) if getattr(exc, "messages", None) else str(exc)
        return JsonResponse({"ok": False, "error": message}, status=400)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def collection_items(request, pk):
    collection = get_user_collection(request.user, pk)
    user_work_id = optional_int(request.POST.get("uw_id"))
    action = request.POST.get("action") or "add"
    if not user_work_id:
        return HttpResponseBadRequest("Не указано произведение")
    user_work = get_object_or_404(UserWork, user=request.user, pk=user_work_id)
    try:
        if action == "remove":
            changed = remove_user_work_from_collection(
                request.user, collection, user_work
            )
        else:
            _item, created = add_user_work_to_collection(
                request.user, collection, user_work
            )
            changed = created
    except ValidationError as exc:
        message = " ".join(exc.messages) if getattr(exc, "messages", None) else str(exc)
        return JsonResponse({"ok": False, "error": message}, status=400)
    return JsonResponse(
        {
            "ok": True,
            "changed": changed,
            "in_collection": action != "remove",
            "collection_id": collection.pk,
        }
    )


@login_required
@require_POST
def collection_items_reorder(request, pk):
    collection = get_user_collection(request.user, pk)
    reorder_collection_items(request.user, collection, parse_ids(request))
    return JsonResponse({"ok": True})


def _collection_mutation_response():
    response = HttpResponse()
    response["HX-Trigger"] = json.dumps(
        {
            "vor:reload-tree": True,
            "vor:close-modal": True,
            "collection-update": True,
        }
    )
    return response


def _collection_form_response(request, template, context, status=200):
    return render(request, template, context, status=status)
