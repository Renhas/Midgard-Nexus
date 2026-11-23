from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse

from .artworks.services import get_user_collection_trees
from .constants import age_rating_options, status_options
from .models import Platform, Tag
from .registry import WORK_TYPE_REGISTRY
from .utils import module_base_context


@login_required
def index(request):
    """Главная страница модуля «Библиотека» — страница произведений."""
    collections = get_user_collection_trees(request.user)
    platforms = list(Platform.objects.all())
    tags = list(Tag.objects.all())
    platform_options = [{"value": p.id, "label": p.name} for p in platforms]
    tags_options = [{"value": p.id, "label": p.name} for p in tags]
    genres_nested = []
    genre_catalog = {}
    for type_key, meta in WORK_TYPE_REGISTRY.items():
        options = [
            {"value": g.id, "label": g.name} for g in meta.genre_model.objects.all()
        ]
        genre_catalog[f"genre_{type_key}"] = [item["value"] for item in options]
        if options:
            genres_nested.append(
                {
                    "title": meta.label_plural,
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
            **module_base_context("artworks"),
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
