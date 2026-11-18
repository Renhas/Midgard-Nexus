from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..catalog import SIMPLE_KINDS, genre_type_meta
from ..services import get_genre, get_simple_attr
from .utils import (
    attr_list_context,
    empty_context,
    genre_item_context,
    simple_item_context,
)


@login_required
@require_GET
def attr_list(request, kind):
    return render(
        request,
        "vor_archives/partials/attributes/attr_list.html",
        attr_list_context(request, kind),
    )


@login_required
@require_GET
def attr_empty(request, kind):
    return render(
        request,
        "vor_archives/partials/attributes/attr_empty.html",
        empty_context(kind),
    )


@login_required
@require_GET
def attr_detail(request, kind, pk):
    if kind == "genres":
        return HttpResponseBadRequest("Не указан тип жанра")
    if kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    obj = get_simple_attr(kind, pk)
    if obj is None:
        raise Http404("Атрибут не найден")
    return render(
        request,
        "vor_archives/partials/attributes/attr_detail.html",
        simple_item_context(request, kind, obj),
    )


@login_required
@require_GET
def genre_detail(request, type_key, pk):
    if genre_type_meta(type_key) is None:
        return HttpResponseBadRequest("Неизвестный тип жанра")
    obj = get_genre(type_key, pk)
    if obj is None:
        raise Http404("Жанр не найден")
    return render(
        request,
        "vor_archives/partials/attributes/attr_detail.html",
        genre_item_context(request, obj, type_key),
    )
