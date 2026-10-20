from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db.models import prefetch_related_objects
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from apps.vor_archives.constants import UserWorkStatusChoices, LOGIN_URL
from apps.vor_archives.templatetags.vor_archives_extras import get_progress_info
from apps.vor_archives.models import UserWork
from ..services import (
    attach_work,
    get_work,
    orphan_works,
    reorder_user_works,
    user_has_work,
)

from .utils import (
    parse_ids,
    progress_meta_for_work,
    wants_json,
    list_response,
)


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_reorder(request):
    reorder_user_works(request.user, parse_ids(request))
    return JsonResponse({"ok": True})


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_attach(request):
    type_key = request.POST.get("work_type")
    work_id = request.POST.get("work_id")
    if not type_key or not work_id:
        return HttpResponseBadRequest("Не указано произведение")
    work = get_work(type_key, work_id)
    if user_has_work(request.user, work):
        if wants_json(request):
            return JsonResponse({"ok": False, "error": "already"}, status=400)
        meta = progress_meta_for_work(work)
        return render(
            request,
            "vor_archives/partials/work_preview_card.html",
            {
                "work": work,
                "work_type": type_key,
                "already": True,
                "progress_max": meta["maximum"],
                "progress_unit": meta["unit"],
                "progress_step": meta["step"],
            },
        )
    status = request.POST.get("status") or UserWorkStatusChoices.PLANNING
    if status not in {choice[0] for choice in UserWorkStatusChoices.choices}:
        return HttpResponseBadRequest("Некорректный статус")
    rating = request.POST.get("rating") or ""
    progress = request.POST.get("progress") or "0"
    try:
        rating_value = int(rating) if rating not in ("", "0") else None
        progress_value = Decimal(progress)
    except (TypeError, ValueError, InvalidOperation):
        return HttpResponseBadRequest("Некорректные данные")
    if rating_value is not None and (rating_value < 1 or rating_value > 10):
        return HttpResponseBadRequest("Некорректный рейтинг")
    if progress_value < 0:
        progress_value = Decimal("0")
    attach_work(
        request.user,
        type_key,
        work_id,
        {
            "status": status,
            "rating": rating_value,
            "progress": progress_value,
        },
    )
    if wants_json(request):
        return JsonResponse({"ok": True})
    return list_response(request, '{"vor:close-overlay": true}')


@login_required(login_url=LOGIN_URL)
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
        "vor_archives/partials/delete_confirm.html",
        {
            "ids": [uw.pk for uw in user_works],
            "count": len(user_works),
            "orphan_titles": [work.title for work in orphans],
        },
    )


@login_required(login_url=LOGIN_URL)
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
        "vor_archives/partials/work_preview_card.html",
        {
            "work": work,
            "work_type": type_key,
            "already": user_has_work(request.user, work),
            "progress_max": meta["maximum"],
            "progress_unit": meta["unit"],
            "progress_step": meta["step"],
        },
    )


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_quick(request, uw_id):
    user_work = get_object_or_404(UserWork, pk=uw_id, user=request.user)
    field = request.POST.get("field")
    value = request.POST.get("value", "")

    if field == "status":
        if value not in {choice[0] for choice in UserWorkStatusChoices.choices}:
            return HttpResponseBadRequest("Некорректный статус")
        user_work.status = value
        if value == UserWorkStatusChoices.COMPLETED:
            meta = get_progress_info(user_work)
            if meta and meta["maximum"] is not None:
                user_work.progress = Decimal(str(meta["maximum"]))
        elif value == UserWorkStatusChoices.IN_PROGRESS:
            user_work.progress = Decimal("0")
    elif field == "progress":
        try:
            progress = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return HttpResponseBadRequest("Некорректный прогресс")
        if progress < 0:
            progress = Decimal("0")
        meta = get_progress_info(user_work)
        if meta and meta["maximum"] is not None:
            maximum = Decimal(str(meta["maximum"]))
            progress = min(progress, maximum)
            if progress >= maximum:
                user_work.status = UserWorkStatusChoices.COMPLETED
        user_work.progress = progress
    elif field == "rating":
        if value in ("", "0"):
            user_work.rating = None
        else:
            try:
                rating = int(value)
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Некорректный рейтинг")
            if rating < 1 or rating > 10:
                return HttpResponseBadRequest("Некорректный рейтинг")
            user_work.rating = rating
    elif field == "is_hidden":
        user_work.is_hidden = value in ("1", "true", "True")
    elif field == "times_completed":
        try:
            times_completed = int(value)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Некорректное число завершений")
        user_work.times_completed = max(times_completed, 0)
    elif field == "owned_platform":
        try:
            platform_id = int(value)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Некорректная платформа")
        work = user_work.work
        if work is None or not work.platforms.filter(pk=platform_id).exists():
            return HttpResponseBadRequest("Платформа не относится к произведению")
        if user_work.owned_platforms.filter(pk=platform_id).exists():
            user_work.owned_platforms.remove(platform_id)
        else:
            user_work.owned_platforms.add(platform_id)
        return JsonResponse(
            {
                "owned_platform_ids": list(
                    user_work.owned_platforms.values_list("pk", flat=True)
                ),
            }
        )
    else:
        return HttpResponseBadRequest("Неизвестное поле")

    user_work.save()
    return JsonResponse(
        {
            "status": user_work.status,
            "progress": float(user_work.progress or 0),
            "times_completed": user_work.times_completed,
            "last_completed_date": (
                user_work.last_completed_date.strftime("%d.%m.%Y")
                if user_work.last_completed_date
                else ""
            ),
        }
    )
