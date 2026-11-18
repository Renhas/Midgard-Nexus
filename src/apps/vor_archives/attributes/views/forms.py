from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ..catalog import SIMPLE_KINDS, genre_type_meta
from ..forms import AttrForm, GenreForm
from ..services import get_genre, get_simple_attr
from .utils import (
    attr_mutation_response,
    attr_tab_or_404,
    form_context,
    genre_item_context,
    require_staff,
    simple_item_context,
)


@login_required
@require_http_methods(["GET", "POST"])
def attr_new(request, kind):
    forbidden = require_staff(request)
    if forbidden:
        return forbidden
    attr_tab_or_404(kind)
    if kind == "genres":
        initial_type = request.GET.get("type") or request.POST.get("type_key") or "book"
        if genre_type_meta(initial_type) is None:
            initial_type = "book"
        if request.method == "POST":
            form = GenreForm(request.POST, initial_type=initial_type)
            if form.is_valid():
                obj, type_key = form.save()
                return attr_mutation_response(
                    request,
                    "vor_archives/partials/attributes/attr_detail.html",
                    genre_item_context(request, obj, type_key),
                )
        else:
            form = GenreForm(initial_type=initial_type)
        return render(
            request,
            "vor_archives/partials/attributes/attr_form.html",
            form_context(
                kind,
                form,
                is_create=True,
                type_label=genre_type_meta(initial_type)["label"],
            ),
        )

    if kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    if request.method == "POST":
        form = AttrForm(request.POST, kind=kind)
        if form.is_valid():
            obj = form.save()
            return attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        form_context(
            kind,
            form,
            is_create=True,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def attr_edit(request, kind, pk):
    forbidden = require_staff(request)
    if forbidden:
        return forbidden
    if kind == "genres" or kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    obj = get_simple_attr(kind, pk)
    if obj is None:
        raise Http404("Атрибут не найден")
    if request.method == "POST":
        form = AttrForm(request.POST, kind=kind, instance=obj)
        if form.is_valid():
            obj = form.save()
            return attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind, instance=obj)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        form_context(
            kind,
            form,
            is_create=False,
            pk=obj.pk,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def genre_edit(request, type_key, pk):
    forbidden = require_staff(request)
    if forbidden:
        return forbidden
    if genre_type_meta(type_key) is None:
        return HttpResponseBadRequest("Неизвестный тип жанра")
    obj = get_genre(type_key, pk)
    if obj is None:
        raise Http404("Жанр не найден")
    if request.method == "POST":
        form = GenreForm(
            request.POST, instance=obj, lock_type=True, initial_type=type_key
        )
        if form.is_valid():
            obj, saved_type = form.save()
            return attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                genre_item_context(request, obj, saved_type),
            )
    else:
        form = GenreForm(instance=obj, lock_type=True, initial_type=type_key)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        form_context(
            "genres",
            form,
            is_create=False,
            type_key=type_key,
            pk=obj.pk,
            type_label=genre_type_meta(type_key)["label"],
            lock_type=True,
        ),
    )
