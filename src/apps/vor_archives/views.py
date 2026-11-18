from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .constants import age_rating_options, status_options
from .dashboard import (
    attrs_payload,
    feed_page,
    heatmap_payload,
    parse_heatmap_year,
    stats_payload,
)
from .dashboard_catalog import DASHBOARD_TABS, DEFAULT_DASH_TAB, get_dash_tab
from .registry import WORK_TYPE_REGISTRY
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

    filter_sections = [
        {"title": "Статус", "options": status_options(), "name": "status"},
        {
            "title": "Возрастной рейтинг",
            "options": age_rating_options(),
            "name": "age_rating",
        },
        {"title": "Теги", "options": tags_options, "name": "tags", "searchable": True},
        {"title": "Жанры", "nested": genres_nested},
        {
            "title": "Платформы",
            "options": platform_options,
            "name": "platform",
            "show_condition": "$store.vorArtworks.workTypes.includes('game')",
            "searchable": True,
        },
    ]

    return render(
        request,
        "vor_archives/artworks.html",
        {
            "module_name": module["name"],
            "module_icon": module["icon"],
            "module_color": module["color"],
            "active_section": "artworks",
            "collections": collections,
            "filter_sections": filter_sections,
            "sort_fields": [
                {"value": "custom", "label": "Свой порядок"},
                {"value": "title", "label": "Название"},
                {"value": "rating", "label": "Рейтинг"},
                {"value": "status", "label": "Статус"},
                {"value": "date_added", "label": "Дата добавления"},
            ],
            "work_types": WORK_TYPE_REGISTRY.values(),
            "page_opts": {
                "listUrl": reverse("vor_archives:artworks:list"),
                "reorderUrl": reverse("vor_archives:artworks:reorder"),
                "searchUrl": reverse("vor_archives:artworks:library_search"),
                "attachUrl": reverse("vor_archives:artworks:attach"),
                "collectionBaseUrl": reverse("vor_archives:collections:index"),
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
