from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ..catalog import SIMPLE_KINDS, genre_type_meta
from ..forms import AttrForm, GenreForm
from ..services import get_genre, get_simple_attr
from .utils import (
    attr_item_context,
    attr_mutation_response,
    attr_tab_or_404,
    form_context,
    staff_required,
)


def _handle_attr_form(request, kind, form, *, on_save, **form_ctx_kwargs):
    if request.method == "POST" and form.is_valid():
        old_name = getattr(form.instance, "name", "") or ""
        changed_fields = [
            str(form.fields[name].label)
            for name in form.changed_data
            if name in form.fields and name != "name"
        ]
        detail_context = on_save(form)
        return attr_mutation_response(
            request,
            "vor_archives/partials/attributes/attr_detail.html",
            detail_context,
            extra_trigger={
                "vor:attr-saved": {
                    "isCreate": bool(form_ctx_kwargs.get("is_create")),
                    "oldName": old_name,
                    "name": detail_context.get("item", {}).get("name", ""),
                    "changedFields": changed_fields,
                }
            },
        )
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        form_context(kind, form, **form_ctx_kwargs),
    )


def _resolved_initial_genre_type(request):
    initial_type = request.GET.get("type") or request.POST.get("type_key") or "book"
    if genre_type_meta(initial_type) is None:
        return "book"
    return initial_type


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def attr_new(request, kind):
    attr_tab_or_404(kind)
    if kind == "genres":
        initial_type = _resolved_initial_genre_type(request)
        form = GenreForm(
            request.POST if request.method == "POST" else None,
            initial_type=initial_type,
        )
        return _handle_attr_form(
            request,
            kind,
            form,
            on_save=lambda f: attr_item_context(request, kind, *f.save()),
            is_create=True,
            type_label=genre_type_meta(initial_type)["label"],
        )

    if kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    form = AttrForm(
        request.POST if request.method == "POST" else None,
        kind=kind,
    )
    return _handle_attr_form(
        request,
        kind,
        form,
        on_save=lambda f: attr_item_context(request, kind, f.save()),
        is_create=True,
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def attr_edit(request, kind, pk):
    if kind == "genres" or kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    obj = get_simple_attr(kind, pk)
    if obj is None:
        raise Http404("Атрибут не найден")
    form = AttrForm(
        request.POST if request.method == "POST" else None,
        kind=kind,
        instance=obj,
    )
    return _handle_attr_form(
        request,
        kind,
        form,
        on_save=lambda f: attr_item_context(request, kind, f.save()),
        is_create=False,
        pk=obj.pk,
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def genre_edit(request, type_key, pk):
    if genre_type_meta(type_key) is None:
        return HttpResponseBadRequest("Неизвестный тип жанра")
    obj = get_genre(type_key, pk)
    if obj is None:
        raise Http404("Жанр не найден")
    form = GenreForm(
        request.POST if request.method == "POST" else None,
        instance=obj,
        lock_type=True,
        initial_type=type_key,
    )
    return _handle_attr_form(
        request,
        "genres",
        form,
        on_save=lambda f: attr_item_context(request, "genres", *f.save()),
        is_create=False,
        type_key=type_key,
        pk=obj.pk,
        type_label=genre_type_meta(type_key)["label"],
        lock_type=True,
    )
