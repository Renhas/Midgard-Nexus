from functools import wraps
import json

from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse

from ..catalog import SIMPLE_KINDS, genre_type_meta, get_attr_tab
from ..services import (
    genre_composite_id,
    genre_work_count,
    list_genre_groups,
    list_simple_attrs,
    simple_work_count,
)


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Недостаточно прав")
        return view_func(request, *args, **kwargs)

    return _wrapped


def attr_tab_or_404(kind):
    tab = get_attr_tab(kind)
    if tab is None:
        raise Http404("Неизвестный тип атрибута")
    return tab


def search_query(request):
    return request.GET.get("q") or request.POST.get("q") or ""


def _item_urls(kind, pk, type_key=None):
    if type_key:
        return {
            "detail_url": reverse(
                "vor_archives:attributes:genre_detail",
                args=[type_key, pk],
            ),
            "edit_url": reverse(
                "vor_archives:attributes:genre_edit",
                args=[type_key, pk],
            ),
        }
    return {
        "detail_url": reverse("vor_archives:attributes:detail", args=[kind, pk]),
        "edit_url": reverse("vor_archives:attributes:edit", args=[kind, pk]),
    }


def attach_item_urls(kind, item):
    item.update(_item_urls(kind, item["pk"], item.get("type_key")))
    return item


def attr_list_context(request, kind):
    tab = attr_tab_or_404(kind)
    if kind == "genres":
        groups, total = list_genre_groups(search_query(request))
        for group in groups:
            for item in group["items"]:
                attach_item_urls(kind, item)
        items = []
        has_items = any(group["items"] for group in groups)
    else:
        items, total = list_simple_attrs(kind, search_query(request))
        for item in items:
            attach_item_urls(kind, item)
        groups = []
        has_items = bool(items)
    return {
        "kind": kind,
        "tab": tab,
        "groups": groups,
        "items": items,
        "total_count": total,
        "has_items": has_items,
        "is_staff": request.user.is_staff,
    }


def attr_item_context(request, kind, obj, type_key=None):
    if kind == "genres":
        meta = genre_type_meta(type_key)
        item = {
            "key": genre_composite_id(type_key, obj.pk),
            "pk": obj.pk,
            "type_key": type_key,
            "type_label": meta["label"],
            "name": obj.name,
            "description": obj.description,
            "work_count": genre_work_count(obj, type_key),
            "has_text": True,
            "empty_text": "Нет описания",
        }
    else:
        meta = SIMPLE_KINDS[kind]
        text_field = meta["text_field"]
        item = {
            "key": str(obj.pk),
            "pk": obj.pk,
            "name": obj.name,
            "description": getattr(obj, text_field) if text_field else "",
            "work_count": simple_work_count(obj, kind),
            "has_text": bool(text_field),
            "empty_text": meta.get("empty_text") or "Нет описания",
        }
    attach_item_urls(kind, item)
    return {
        "kind": kind,
        "tab": get_attr_tab(kind),
        "item": item,
        "is_staff": request.user.is_staff,
    }


def empty_context(kind):
    tab = attr_tab_or_404(kind)
    return {
        "kind": kind,
        "tab": tab,
        "empty_prompt": tab["empty_prompt"],
    }


def form_context(
    kind, form, *, is_create, type_key=None, pk=None, type_label=None, lock_type=False
):
    tab = get_attr_tab(kind)
    has_text = kind == "genres" or bool(SIMPLE_KINDS.get(kind, {}).get("text_field"))
    if is_create:
        save_url = reverse("vor_archives:attributes:new", args=[kind])
        cancel_url = reverse("vor_archives:attributes:empty", args=[kind])
    else:
        urls = _item_urls(kind, pk, type_key if kind == "genres" else None)
        save_url = urls["edit_url"]
        cancel_url = urls["detail_url"]
    return {
        "kind": kind,
        "tab": tab,
        "form": form,
        "is_create": is_create,
        "show_type": kind == "genres",
        "has_text": has_text,
        "lock_type": lock_type,
        "type_label": type_label,
        "type_key": type_key,
        "pk": pk,
        "save_url": save_url,
        "cancel_url": cancel_url,
    }


def attr_mutation_response(
    request, detail_template, detail_context, extra_trigger=None
):
    response = render(request, detail_template, detail_context)
    triggers = {"vor:attr-list-refresh": True}
    if extra_trigger:
        triggers.update(extra_trigger)
    response["HX-Trigger"] = json.dumps(triggers)
    return response
