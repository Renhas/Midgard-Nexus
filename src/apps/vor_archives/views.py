import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import age_rating_options, status_options
from .dashboard import (
    attrs_payload,
    feed_page,
    heatmap_payload,
    parse_heatmap_year,
    stats_payload,
)
from .dashboard_catalog import DASHBOARD_TABS, DEFAULT_DASH_TAB, get_dash_tab
from .attr_catalog import (
    ATTR_TABS,
    DEFAULT_KIND,
    SIMPLE_KINDS,
    genre_composite_id,
    genre_type_meta,
    genre_work_count,
    get_attr_tab,
    get_genre,
    get_simple_attr,
    list_genre_groups,
    list_simple_attrs,
    parse_genre_ids,
    parse_simple_ids,
    simple_work_count,
)
from .forms import AttrForm, GenreForm
from .models import (
    BookGenre,
    FilmGenre,
    GameGenre,
    Platform,
    Tag,
)
from .artworks.services import (
    get_user_collection_trees,
)


def _module_context():
    """Возвращает общие переменные шаблона для модуля vor_archives."""
    return next(m for m in settings.MODULES if m["url_name"] == "vor_archives")


@login_required
def index(request):
    """Главная страница модуля «Библиотека» — страница произведений."""
    module = _module_context()
    collections = get_user_collection_trees(request.user)
    platforms = list(Platform.objects.all())
    tags = list(Tag.objects.all())
    platform_options = [{"value": p.id, "label": p.name} for p in platforms]
    tags_options = [{"value": p.id, "label": p.name} for p in tags]
    genre_models = [
        ("book", BookGenre, "Книги"),
        ("film", FilmGenre, "Фильмы"),
        ("game", GameGenre, "Игры"),
    ]
    genres_nested = []
    genre_catalog = {}
    for type_key, model, label in genre_models:
        options = [{"value": g.id, "label": g.name} for g in model.objects.all()]
        genre_catalog[f"genre_{type_key}"] = [item["value"] for item in options]
        if options:
            genres_nested.append(
                {
                    "title": label,
                    "options": options,
                    "name": f"genre_{type_key}",
                    "show_condition": f"$store.vorArtworks.workTypes.includes('{type_key}')",
                }
            )

    return render(
        request,
        "vor_archives/artworks.html",
        {
            "module_name": module["name"],
            "module_icon": module["icon"],
            "module_color": module["color"],
            "active_section": "artworks",
            "collections": collections,
            "status_options": status_options(),
            "age_rating_options": age_rating_options(),
            "tags_options": tags_options,
            "platform_options": platform_options,
            "genres_nested": genres_nested,
            "sort_fields": [
                {"value": "custom", "label": "Свой порядок"},
                {"value": "title", "label": "Название"},
                {"value": "rating", "label": "Рейтинг"},
                {"value": "status", "label": "Статус"},
                {"value": "date_added", "label": "Дата добавления"},
            ],
            "page_opts": {
                "listUrl": reverse("vor_archives:artworks:list"),
                "reorderUrl": reverse("vor_archives:artworks:reorder"),
                "searchUrl": reverse("vor_archives:artworks:library_search"),
                "attachUrl": reverse("vor_archives:artworks:attach"),
                "collectionTreeUrl": reverse("vor_archives:collections:tree"),
                "collectionReorderUrl": reverse("vor_archives:collections:reorder"),
                "collectionNewUrl": reverse("vor_archives:collections:new"),
                "isStaff": request.user.is_staff,
                "filterCatalog": {
                    "status": [item["value"] for item in status_options()],
                    "age_rating": [item["value"] for item in age_rating_options()],
                    "tags": [item["value"] for item in tags_options],
                    "genre_book": genre_catalog.get("genre_book", []),
                    "genre_film": genre_catalog.get("genre_film", []),
                    "genre_game": genre_catalog.get("genre_game", []),
                    "platform": [item["value"] for item in platform_options],
                },
            },
        },
    )


@login_required
def dashboard(request):
    """Страница дашборда — редирект на вкладку статистики."""
    return redirect("vor_archives:dashboard_tab", tab=DEFAULT_DASH_TAB)


def _dashboard_shell(request, tab_kind, extra=None):
    tab = get_dash_tab(tab_kind)
    if tab is None:
        raise Http404("Неизвестная вкладка дашборда")
    module = _module_context()
    context = {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_color": module["color"],
        "active_section": "dashboard",
        "hide_right": True,
        "dash_kind": tab_kind,
        "dash_tabs": DASHBOARD_TABS,
        "dash_tab": tab,
    }
    if extra:
        context.update(extra)
    return render(request, "vor_archives/dashboard.html", context)


@login_required
def dashboard_tab(request, tab):
    """Оболочка дашборда для выбранной вкладки."""
    if get_dash_tab(tab) is None:
        raise Http404("Неизвестная вкладка дашборда")
    extra = {}
    if tab == "stats":
        extra.update(stats_payload(request.user))
    elif tab == "attrs":
        extra.update(attrs_payload(request.user))
    elif tab == "activity":
        items, has_more = feed_page(request.user)
        extra.update(
            {
                "feed_items": items,
                "feed_has_more": has_more,
                "feed_next_offset": len(items),
                "heatmap": heatmap_payload(
                    request.user,
                    year=parse_heatmap_year(request.GET.get("year")),
                ),
            }
        )
    return _dashboard_shell(request, tab, extra)


@login_required
@require_GET
def dashboard_feed(request):
    try:
        offset = max(int(request.GET.get("offset") or 0), 0)
    except (TypeError, ValueError):
        offset = 0
    items, has_more = feed_page(request.user, offset=offset)
    return render(
        request,
        "vor_archives/partials/dashboard/dash_feed_items.html",
        {
            "feed_items": items,
            "feed_has_more": has_more,
            "feed_next_offset": offset + len(items),
        },
    )


@login_required
@require_GET
def dashboard_heatmap(request):
    year = parse_heatmap_year(request.GET.get("year"))
    return render(
        request,
        "vor_archives/partials/dashboard/dash_heatmap.html",
        {"heatmap": heatmap_payload(request.user, year=year)},
    )


@login_required
def attributes(request):
    """Страница атрибутов — редирект на первую готовую вкладку."""
    return redirect("vor_archives:attributes_kind", kind=DEFAULT_KIND)


@login_required
def attributes_kind(request, kind):
    """Оболочка страницы атрибутов для выбранной вкладки."""
    tab = get_attr_tab(kind)
    if tab is None:
        raise Http404("Неизвестный тип атрибута")
    module = _module_context()
    return render(
        request,
        "vor_archives/attributes.html",
        {
            "module_name": module["name"],
            "module_icon": module["icon"],
            "module_color": module["color"],
            "active_section": "attributes",
            "hide_right": True,
            "attr_kind": kind,
            "attr_label": tab["label"],
            "attr_icon": tab["icon"],
            "attr_tabs": ATTR_TABS,
            "tab": tab,
            "search_placeholder": tab["search_placeholder"],
            "empty_prompt": tab["empty_prompt"],
            "is_staff": request.user.is_staff,
        },
    )


def _require_staff(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Недостаточно прав")
    return None


def _attr_tab_or_404(kind):
    tab = get_attr_tab(kind)
    if tab is None:
        raise Http404("Неизвестный тип атрибута")
    return tab


def _query(request):
    return request.GET.get("q") or request.POST.get("q") or ""


def _attach_item_urls(kind, item):
    if item.get("type_key"):
        item["detail_url"] = reverse(
            "vor_archives:genre_detail", args=[item["type_key"], item["pk"]]
        )
        item["edit_url"] = reverse(
            "vor_archives:genre_edit", args=[item["type_key"], item["pk"]]
        )
    else:
        item["detail_url"] = reverse(
            "vor_archives:attr_detail", args=[kind, item["pk"]]
        )
        item["edit_url"] = reverse("vor_archives:attr_edit", args=[kind, item["pk"]])
    return item


def _attr_list_context(request, kind):
    tab = _attr_tab_or_404(kind)
    if kind == "genres":
        groups, total = list_genre_groups(_query(request))
        for group in groups:
            for item in group["items"]:
                _attach_item_urls(kind, item)
        items = []
        has_items = any(group["items"] for group in groups)
    else:
        items, total = list_simple_attrs(kind, _query(request))
        for item in items:
            _attach_item_urls(kind, item)
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


def _genre_item_context(request, obj, type_key):
    meta = genre_type_meta(type_key)
    item = _attach_item_urls(
        "genres",
        {
            "key": genre_composite_id(type_key, obj.pk),
            "pk": obj.pk,
            "type_key": type_key,
            "type_label": meta["label"],
            "name": obj.name,
            "description": obj.description,
            "work_count": genre_work_count(obj, type_key),
            "has_text": True,
            "empty_text": "Нет описания",
        },
    )
    return {
        "kind": "genres",
        "tab": get_attr_tab("genres"),
        "item": item,
        "is_staff": request.user.is_staff,
    }


def _simple_item_context(request, kind, obj):
    meta = SIMPLE_KINDS[kind]
    text_field = meta["text_field"]
    item = _attach_item_urls(
        kind,
        {
            "key": str(obj.pk),
            "pk": obj.pk,
            "name": obj.name,
            "description": getattr(obj, text_field) if text_field else "",
            "work_count": simple_work_count(obj, kind),
            "has_text": bool(text_field),
            "empty_text": meta.get("empty_text") or "Нет описания",
        },
    )
    return {
        "kind": kind,
        "tab": get_attr_tab(kind),
        "item": item,
        "is_staff": request.user.is_staff,
    }


def _empty_context(kind):
    tab = _attr_tab_or_404(kind)
    return {
        "kind": kind,
        "tab": tab,
        "empty_prompt": tab["empty_prompt"],
    }


def _form_context(
    kind, form, *, is_create, type_key=None, pk=None, type_label=None, lock_type=False
):
    tab = get_attr_tab(kind)
    has_text = kind == "genres" or bool(SIMPLE_KINDS.get(kind, {}).get("text_field"))
    cancel_url = reverse("vor_archives:attr_empty", args=[kind])
    if not is_create:
        if kind == "genres":
            cancel_url = reverse("vor_archives:genre_detail", args=[type_key, pk])
            save_url = reverse("vor_archives:genre_edit", args=[type_key, pk])
        else:
            cancel_url = reverse("vor_archives:attr_detail", args=[kind, pk])
            save_url = reverse("vor_archives:attr_edit", args=[kind, pk])
    else:
        save_url = reverse("vor_archives:attr_new", args=[kind])
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


def _attr_mutation_response(
    request, detail_template, detail_context, extra_trigger=None
):
    response = render(request, detail_template, detail_context)
    triggers = {"vor:attr-list-refresh": True}
    if extra_trigger:
        triggers.update(extra_trigger)
    response["HX-Trigger"] = json.dumps(triggers)
    return response


@login_required
@require_GET
def attr_list(request, kind):
    return render(
        request,
        "vor_archives/partials/attributes/attr_list.html",
        _attr_list_context(request, kind),
    )


@login_required
@require_GET
def attr_empty(request, kind):
    return render(
        request,
        "vor_archives/partials/attributes/attr_empty.html",
        _empty_context(kind),
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
        _simple_item_context(request, kind, obj),
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
        _genre_item_context(request, obj, type_key),
    )


@login_required
@require_http_methods(["GET", "POST"])
def attr_new(request, kind):
    forbidden = _require_staff(request)
    if forbidden:
        return forbidden
    _attr_tab_or_404(kind)
    if kind == "genres":
        initial_type = request.GET.get("type") or request.POST.get("type_key") or "book"
        if genre_type_meta(initial_type) is None:
            initial_type = "book"
        if request.method == "POST":
            form = GenreForm(request.POST, initial_type=initial_type)
            if form.is_valid():
                obj, type_key = form.save()
                return _attr_mutation_response(
                    request,
                    "vor_archives/partials/attributes/attr_detail.html",
                    _genre_item_context(request, obj, type_key),
                )
        else:
            form = GenreForm(initial_type=initial_type)
        return render(
            request,
            "vor_archives/partials/attributes/attr_form.html",
            _form_context(
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
            return _attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                _simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        _form_context(
            kind,
            form,
            is_create=True,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def attr_edit(request, kind, pk):
    forbidden = _require_staff(request)
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
            return _attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                _simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind, instance=obj)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        _form_context(
            kind,
            form,
            is_create=False,
            pk=obj.pk,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def genre_edit(request, type_key, pk):
    forbidden = _require_staff(request)
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
            return _attr_mutation_response(
                request,
                "vor_archives/partials/attributes/attr_detail.html",
                _genre_item_context(request, obj, saved_type),
            )
    else:
        form = GenreForm(instance=obj, lock_type=True, initial_type=type_key)
    return render(
        request,
        "vor_archives/partials/attributes/attr_form.html",
        _form_context(
            "genres",
            form,
            is_create=False,
            type_key=type_key,
            pk=obj.pk,
            type_label=genre_type_meta(type_key)["label"],
            lock_type=True,
        ),
    )


def _genre_delete_items(pairs):
    items = []
    for type_key, pk in pairs:
        obj = get_genre(type_key, pk)
        if obj is None:
            continue
        items.append(
            {
                "key": genre_composite_id(type_key, pk),
                "type_key": type_key,
                "pk": pk,
                "name": obj.name,
                "type_label": genre_type_meta(type_key)["label"],
                "work_count": genre_work_count(obj, type_key),
                "obj": obj,
            }
        )
    return items


def _simple_delete_items(kind, pks):
    items = []
    for pk in pks:
        obj = get_simple_attr(kind, pk)
        if obj is None:
            continue
        items.append(
            {
                "key": str(pk),
                "pk": pk,
                "name": obj.name,
                "work_count": simple_work_count(obj, kind),
                "obj": obj,
            }
        )
    return items


@login_required
@require_GET
def attr_delete_preview(request, kind):
    forbidden = _require_staff(request)
    if forbidden:
        return forbidden
    tab = _attr_tab_or_404(kind)
    if kind == "genres":
        items = _genre_delete_items(parse_genre_ids(request.GET.getlist("ids")))
    elif kind in SIMPLE_KINDS:
        items = _simple_delete_items(kind, parse_simple_ids(request.GET.getlist("ids")))
    else:
        raise Http404("Неизвестный тип атрибута")
    if len(items) == 1:
        delete_text = tab["delete_one"].format(name=items[0]["name"])
    else:
        delete_text = tab["delete_many"].format(count=len(items))
    return render(
        request,
        "vor_archives/partials/attributes/attr_delete_confirm.html",
        {
            "kind": kind,
            "tab": tab,
            "items": items,
            "count": len(items),
            "delete_text": delete_text,
            "linked_count": sum(item["work_count"] for item in items),
            "delete_url": reverse("vor_archives:attr_delete", args=[kind]),
        },
    )


@login_required
@require_POST
def attr_delete(request, kind):
    forbidden = _require_staff(request)
    if forbidden:
        return forbidden
    _attr_tab_or_404(kind)
    if kind == "genres":
        items = _genre_delete_items(parse_genre_ids(request.POST.getlist("ids")))
    elif kind in SIMPLE_KINDS:
        items = _simple_delete_items(
            kind, parse_simple_ids(request.POST.getlist("ids"))
        )
    else:
        raise Http404("Неизвестный тип атрибута")
    with transaction.atomic():
        for item in items:
            item["obj"].delete()
    return _attr_mutation_response(
        request,
        "vor_archives/partials/attributes/attr_empty.html",
        _empty_context(kind),
        extra_trigger={"vor:close-attr-modal": True},
    )
