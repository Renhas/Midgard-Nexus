from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.vor_archives.constants import LOGIN_URL
from apps.vor_archives.registry import WORK_MODELS
from ..services import (
    search_library_works,
    search_works,
    user_owned_work_ids,
)


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_library_search(request):
    result = search_library_works(request.user, request.GET.get("q") or "")
    for item in result["owned"]:
        item["detail_url"] = reverse(
            "vor_archives:artworks:detail", args=[item["uw_id"]]
        )
    for item in result["other"]:
        item["detail_url"] = reverse(
            "vor_archives:artworks:work", args=[item["type_key"], item["work_id"]]
        )
    return render(
        request,
        "vor_archives/partials/library_search_results.html",
        {
            **result,
            "query": (request.GET.get("q") or "").strip(),
        },
    )


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_search(request):
    type_key = request.GET.get("work_type") or request.GET.get("type") or "book"
    query = (request.GET.get("q") or request.GET.get("title") or "").strip()
    model = WORK_MODELS.get(type_key)
    works = []
    already_owned = False
    if model and len(query) >= 1:
        owned_ids = user_owned_work_ids(request.user, type_key)
        already_owned = model.objects.filter(
            pk__in=owned_ids, title__iexact=query
        ).exists()
        works = list(
            model.objects.filter(title__icontains=query)
            .exclude(pk__in=owned_ids)
            .order_by("title")[:10]
        )
    return render(
        request,
        "vor_archives/partials/work_suggestions.html",
        {
            "works": works,
            "work_type": type_key,
            "query": query,
            "already_owned": already_owned,
        },
    )


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_relation_search(request):
    results = search_works(
        request.GET.get("q") or "",
        exclude_type=request.GET.get("exclude_type"),
        exclude_id=request.GET.get("exclude_id"),
    )
    return JsonResponse({"results": results})
