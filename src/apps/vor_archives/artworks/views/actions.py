from django.contrib.auth.decorators import login_required
from django.db.models import prefetch_related_objects
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from apps.vor_archives.artworks.forms import AttachWorkForm, QuickUpdateForm
from apps.vor_archives.models import UserWork
from ..services import (
    AlreadyAttached,
    PlatformNotRelated,
    attach_work_from_form,
    get_work,
    orphan_works,
    quick_update,
    reorder_user_works,
    user_has_work,
)

from .utils import (
    parse_ids,
    progress_meta_for_work,
    wants_json,
    list_response,
)


@login_required
@require_POST
def artwork_reorder(request):
    reorder_user_works(request.user, parse_ids(request))
    return JsonResponse({"ok": True})


@login_required
@require_POST
def artwork_attach(request):
    form = AttachWorkForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Некорректные данные")

    try:
        attach_work_from_form(request.user, form)
    except AlreadyAttached as exc:
        return _attach_already_response(
            request, exc.work, form.cleaned_data["work_type"]
        )

    if wants_json(request):
        return JsonResponse({"ok": True})
    return list_response(request, '{"vor:close-overlay": true}')


def _attach_already_response(request, work, type_key):
    if wants_json(request):
        return JsonResponse({"ok": False, "error": "already"}, status=400)
    meta = progress_meta_for_work(work)
    return render(
        request,
        "vor_archives/partials/common/work_preview_card.html",
        {
            "work": work,
            "work_type": type_key,
            "already": True,
            "progress_max": meta["maximum"],
            "progress_unit": meta["unit"],
            "progress_step": meta["step"],
        },
    )


@login_required
@require_GET
def artwork_delete_preview(request):
    ids = parse_ids(request)
    user_works = list(
        UserWork.objects.filter(user=request.user, pk__in=ids).select_related(
            "work_content_type"
        )
    )
    prefetch_related_objects(user_works, "work")
    orphans = orphan_works(user_works)
    return render(
        request,
        "vor_archives/partials/artworks/list/delete_confirm.html",
        {
            "ids": [uw.pk for uw in user_works],
            "count": len(user_works),
            "orphan_titles": [work.title for work in orphans],
        },
    )


@login_required
@require_GET
def artwork_preview(request):
    type_key = request.GET.get("type") or request.GET.get("work_type") or "book"
    work_id = request.GET.get("work_id")
    if not work_id:
        return HttpResponseBadRequest("Не указано произведение")
    work = get_work(type_key, work_id)
    meta = progress_meta_for_work(work)
    return render(
        request,
        "vor_archives/partials/common/work_preview_card.html",
        {
            "work": work,
            "work_type": type_key,
            "already": user_has_work(request.user, work),
            "progress_max": meta["maximum"],
            "progress_unit": meta["unit"],
            "progress_step": meta["step"],
        },
    )


@login_required
@require_POST
def artwork_quick(request, uw_id):
    user_work = get_object_or_404(UserWork, pk=uw_id, user=request.user)
    form = QuickUpdateForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Некорректные данные")
    try:
        payload = quick_update(
            user_work, form.cleaned_data["field"], form.cleaned_data["value"]
        )
    except PlatformNotRelated:
        return HttpResponseBadRequest("Платформа не относится к произведению")
    return JsonResponse(payload)
