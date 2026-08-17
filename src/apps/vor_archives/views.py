import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import prefetch_related_objects
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import (
    AgeRatingChoices,
    FilmTypeChoices,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
)
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
from .forms import WORK_FORMS, AttrForm, GenreForm, UserWorkEditForm
from .templatetags.vor_archives_extras import get_progress_info
from .models import (
    BookGenre,
    Collection,
    FilmGenre,
    GameGenre,
    Person,
    Platform,
    Tag,
    UserWork,
)
from .services import (
    WORK_MODELS,
    attach_work,
    clamp_progress_for_work,
    delete_user_works,
    get_user_work,
    get_work,
    orphan_works,
    search_works,
    sync_work_relations,
    user_has_work,
    user_has_work_title,
    user_owned_work_ids,
    work_relation_items,
    work_type_key,
)

LOGIN_URL = "users:login"


def _module_context():
    """Возвращает общие переменные шаблона для модуля vor_archives."""
    return next(m for m in settings.MODULES if m["url_name"] == "vor_archives")


def _user_works_qs(user):
    user_works = UserWork.objects.filter(user=user).select_related(
        "work_content_type"
    ).order_by("order_position", "-date_added")
    prefetch_related_objects(user_works, "work")
    return user_works


def _list_response(request, trigger=None):
    response = render(
        request,
        "vor_archives/partials/artwork_list.html",
        {"user_works": _user_works_qs(request.user)},
    )
    if trigger:
        response["HX-Trigger"] = trigger
        response["HX-Retarget"] = "#artwork-list"
        response["HX-Reswap"] = "outerHTML"
    return response


def _progress_unit(work=None, type_key=None, film_type=None):
    key = type_key or (work_type_key(work) if work else "")
    if key == "book":
        return "стр."
    if key == "game":
        return "ч."
    if key == "film":
        f_type = film_type or getattr(work, "film_type", None)
        if f_type == FilmTypeChoices.TV_SHOW:
            return "эп."
        return "мин."
    return ""


def _work_form_class(type_key):
    try:
        return WORK_FORMS[type_key]
    except KeyError:
        return None


@login_required(login_url=LOGIN_URL)
def index(request):
    """Главная страница модуля «Библиотека» — страница произведений."""
    module = _module_context()
    collections = Collection.objects.filter(user=request.user, parent=None)
    status_options = [{"value": v, "label": l} for v, l in UserWorkStatusChoices.choices]
    age_rating_options = [{"value": v, "label": l} for v, l in AgeRatingChoices.choices]
    platform_options = [{"value": p.id, "label": p.name} for p in Platform.objects.all()]
    tags_options = [{"value": p.id, "label": p.name} for p in Tag.objects.all()]
    genre_models = [
        ("book", BookGenre, "Книги"),
        ("film", FilmGenre, "Фильмы"),
        ("game", GameGenre, "Игры"),
    ]
    genres_nested = []
    for type_key, model, label in genre_models:
        options = [{"value": g.id, "label": g.name} for g in model.objects.all()]
        if options:
            genres_nested.append({
                "title": label,
                "options": options,
                "name": f"genre_{type_key}",
                "show_condition": f"workTypes.includes('{type_key}')",
            })

    return render(request, "vor_archives/artworks.html", {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_color": module["color"],
        "active_section": "artworks",
        "collections": collections,
        "status_options": status_options,
        "age_rating_options": age_rating_options,
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
        "sort_field_default": "custom",
        "sort_order_asc": True,
        "work_types": ["book", "film", "game"],
    })


@login_required(login_url=LOGIN_URL)
def dashboard(request):
    """Страница дашборда модуля «Библиотека»."""
    module = _module_context()
    return render(request, "vor_archives/dashboard.html", {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_color": module["color"],
        "active_section": "dashboard",
    })


@login_required(login_url=LOGIN_URL)
def attributes(request):
    """Страница атрибутов — редирект на первую готовую вкладку."""
    return redirect("vor_archives:attributes_kind", kind=DEFAULT_KIND)


@login_required(login_url=LOGIN_URL)
def attributes_kind(request, kind):
    """Оболочка страницы атрибутов для выбранной вкладки."""
    tab = get_attr_tab(kind)
    if tab is None:
        raise Http404("Неизвестный тип атрибута")
    module = _module_context()
    return render(request, "vor_archives/attributes.html", {
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
    })


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_list(request):
    return render(
        request,
        "vor_archives/partials/artwork_list.html",
        {"user_works": _user_works_qs(request.user)},
    )


def _prefetch_work(work, user_work=None):
    type_key = work_type_key(work)
    related = ["authors", "tags", "genres"]
    if type_key == "game":
        related.append("platforms")
    prefetch_related_objects([work], *related)
    if user_work is not None:
        prefetch_related_objects([user_work], "owned_platforms")
    return type_key


def _chip_payload(items, tip_field="description"):
    payload = []
    for item in items:
        payload.append({
            "id": item.pk,
            "name": item.name,
            "tip": getattr(item, tip_field, "") or "",
        })
    return payload


def _attr_catalog(type_key):
    genre_model = {"book": BookGenre, "film": FilmGenre, "game": GameGenre}[type_key]
    return {
        "authors": _chip_payload(Person.objects.order_by("name"), "bio"),
        "genres": _chip_payload(genre_model.objects.order_by("name")),
        "tags": _chip_payload(Tag.objects.order_by("name")),
        "platforms": _chip_payload(Platform.objects.order_by("name"), "") if type_key == "game" else [],
    }


def _all_attr_catalogs():
    return {key: _attr_catalog(key) for key in WORK_FORMS}


def _progress_meta_for_work(work):
    type_key = work_type_key(work)
    if type_key == "book":
        return {"maximum": work.pages, "unit": "стр.", "step": 1}
    if type_key == "game":
        return {"maximum": None, "unit": "ч.", "step": 0.5}
    if getattr(work, "film_type", None) == FilmTypeChoices.TV_SHOW:
        return {"maximum": work.episode_count, "unit": "эп.", "step": 1}
    return {"maximum": getattr(work, "duration_minutes", None), "unit": "мин.", "step": 1}


def _wants_json(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


STATUS_LABELS_RU = {
    UserWorkStatusChoices.PLANNING: "Запланировано",
    UserWorkStatusChoices.IN_PROGRESS: "В процессе",
    UserWorkStatusChoices.COMPLETED: "Завершено",
    UserWorkStatusChoices.DROPPED: "Брошено",
}


RELATION_TYPE_OPTIONS = [
    {"value": WorkRelationTypeChoices.SEQUEL, "label": "Продолжение"},
    {"value": WorkRelationTypeChoices.SPIN_OFF, "label": "Спин-офф"},
    {"value": WorkRelationTypeChoices.ADAPTATION, "label": "Адаптация"},
    {"value": WorkRelationTypeChoices.REMAKE, "label": "Ремейк"},
    {"value": WorkRelationTypeChoices.OTHER, "label": "Связано"},
]


def _parse_id_list(request, name):
    values = []
    for raw in request.POST.getlist(name):
        for part in str(raw).split(","):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(int(part))
            except ValueError:
                continue
    return values


def _parse_relations_payload(request):
    raw = request.POST.get("relations_json") or "[]"
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    parsed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        entry = {
            "id": item.get("id") or None,
            "relation_type": item.get("relation_type") or WorkRelationTypeChoices.OTHER,
            "type_key": item.get("type_key"),
            "work_id": item.get("work_id"),
        }
        if entry["id"]:
            try:
                entry["id"] = int(entry["id"])
            except (TypeError, ValueError):
                entry["id"] = None
        if entry["work_id"]:
            try:
                entry["work_id"] = int(entry["work_id"])
            except (TypeError, ValueError):
                entry["work_id"] = None
        parsed.append(entry)
    return parsed


def _detail_context(request, work, user_work=None, work_form=None, user_work_form=None, editing=False, global_edit=False):
    type_key = work_type_key(work)
    owned = user_work is not None
    if owned:
        progress_meta = get_progress_info(user_work) or {}
    else:
        work_meta = _progress_meta_for_work(work)
        progress_meta = {
            "value": 0,
            "maximum": work_meta["maximum"],
            "unit": work_meta["unit"],
            "step": work_meta["step"],
        }
    owned_platform_ids = []
    if owned:
        owned_platform_ids = list(user_work.owned_platforms.values_list("pk", flat=True))
    catalog = _attr_catalog(type_key)
    save_url = (
        reverse("vor_archives:artwork_detail", args=[user_work.pk])
        if owned
        else reverse("vor_archives:artwork_work", args=[type_key, work.pk])
    )
    return {
        "user_work": user_work,
        "owned": owned,
        "work": work,
        "work_type": type_key,
        "work_form": work_form,
        "user_work_form": user_work_form,
        "is_staff": request.user.is_staff,
        "editing": editing,
        "global_edit": global_edit,
        "progress_unit": _progress_unit(work),
        "progress_meta": progress_meta,
        "hide_platforms": type_key != "game" or not owned,
        "owned_platform_ids": owned_platform_ids,
        "status_choices": [
            (value, STATUS_LABELS_RU.get(value, label))
            for value, label in UserWorkStatusChoices.choices
        ],
        "age_rating_choices": AgeRatingChoices.choices,
        "work_relations": work_relation_items(work),
        "overlay_opts": {
            "editing": editing,
            "globalEdit": global_edit,
            "owned": owned,
            "isStaff": request.user.is_staff,
            "workType": type_key,
            "workId": work.pk,
            "filmType": getattr(work, "film_type", None) or "movie",
            "status": user_work.status if owned else "planning",
            "statusChoices": [
                {"value": value, "label": STATUS_LABELS_RU.get(value, label)}
                for value, label in UserWorkStatusChoices.choices
            ],
            "attachUrl": reverse("vor_archives:artwork_attach"),
            "rating": (user_work.rating or 0) if owned else 0,
            "isHidden": user_work.is_hidden if owned else False,
            "progress": progress_meta.get("value", 0),
            "progressMax": progress_meta.get("maximum"),
            "progressUnit": progress_meta.get("unit", ""),
            "progressStep": progress_meta.get("step", 1),
            "timesCompleted": user_work.times_completed if owned else 0,
            "lastCompletedDate": (
                user_work.last_completed_date.strftime("%d.%m.%Y")
                if owned and user_work.last_completed_date
                else ""
            ),
            "quickUrl": (
                reverse("vor_archives:artwork_quick", args=[user_work.pk])
                if owned
                else ""
            ),
            "listUrl": reverse("vor_archives:artwork_list"),
            "saveUrl": save_url,
            "relationSearchUrl": reverse("vor_archives:artwork_relation_search"),
            "title": work.title,
            "description": work.description or "",
            "releaseDate": work.release_date.isoformat() if work.release_date else "",
            "ageRating": work.age_rating or "",
            "externalLink": work.external_link or "",
            "pages": getattr(work, "pages", None),
            "durationMinutes": getattr(work, "duration_minutes", None),
            "episodeCount": getattr(work, "episode_count", None),
            "coverUrl": work.cover.url if work.cover else "",
            "authors": _chip_payload(work.authors.all(), "bio"),
            "genres": _chip_payload(work.genres.all()),
            "tags": _chip_payload(work.tags.all()),
            "platforms": _chip_payload(work.platforms.all(), "") if type_key == "game" else [],
            "ownedPlatformIds": owned_platform_ids,
            "catalog": catalog,
            "relations": work_relation_items(work),
            "relationTypes": RELATION_TYPE_OPTIONS,
            "ageChoices": [
                {"value": value, "label": label}
                for value, label in AgeRatingChoices.choices
            ],
        },
    }


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_detail(request, uw_id):
    user_work = get_object_or_404(UserWork, pk=uw_id, user=request.user)
    work = user_work.work
    if work is None:
        return HttpResponseBadRequest("Произведение не найдено")
    return _artwork_overlay_response(request, work, user_work)


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_work(request, type_key, work_id):
    if type_key not in WORK_MODELS:
        return HttpResponseBadRequest("Неизвестный тип")
    work = get_work(type_key, work_id)
    user_work = get_user_work(request.user, work)
    return _artwork_overlay_response(request, work, user_work)


def _artwork_overlay_response(request, work, user_work=None):
    type_key = _prefetch_work(work, user_work)
    work_form_class = _work_form_class(type_key)

    if request.method == "POST":
        if not request.user.is_staff:
            return HttpResponseBadRequest("Недостаточно прав")
        post = request.POST.copy()
        for name in ("authors", "tags", "genres", "platforms"):
            ids = _parse_id_list(request, name)
            post.setlist(name, [str(item) for item in ids])
        work_form = work_form_class(post, request.FILES, instance=work)
        if work_form.is_valid():
            saved = work_form.save()
            if post.get("cover_clear") == "1" and not request.FILES.get("cover"):
                if saved.cover:
                    saved.cover.delete(save=False)
                saved.cover = None
                saved.save(update_fields=["cover"])
            try:
                sync_work_relations(saved, _parse_relations_payload(request))
            except ValidationError as error:
                work_form.add_error(None, error)
            else:
                clamp_progress_for_work(saved)
                if type_key == "game" and user_work is not None:
                    valid_ids = set(saved.platforms.values_list("pk", flat=True))
                    stale_ids = [
                        pk
                        for pk in user_work.owned_platforms.values_list("pk", flat=True)
                        if pk not in valid_ids
                    ]
                    if stale_ids:
                        user_work.owned_platforms.remove(*stale_ids)
                _prefetch_work(saved, user_work)
                return render(
                    request,
                    "vor_archives/partials/artwork_overlay.html",
                    _detail_context(
                        request, saved, user_work,
                        work_form_class(instance=saved),
                        UserWorkEditForm(instance=user_work) if user_work is not None else None,
                    ),
                )
        return render(
            request,
            "vor_archives/partials/artwork_overlay.html",
            _detail_context(
                request, work, user_work, work_form,
                UserWorkEditForm(instance=user_work) if user_work is not None else None,
                editing=True, global_edit=True,
            ),
        )

    return render(
        request,
        "vor_archives/partials/artwork_overlay.html",
        _detail_context(
            request, work, user_work,
            work_form_class(instance=work),
            UserWorkEditForm(instance=user_work) if user_work is not None else None,
        ),
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
        return JsonResponse({
            "owned_platform_ids": list(user_work.owned_platforms.values_list("pk", flat=True)),
        })
    else:
        return HttpResponseBadRequest("Неизвестное поле")

    user_work.save()
    return JsonResponse({
        "status": user_work.status,
        "progress": float(user_work.progress or 0),
        "times_completed": user_work.times_completed,
        "last_completed_date": (
            user_work.last_completed_date.strftime("%d.%m.%Y")
            if user_work.last_completed_date
            else ""
        ),
    })


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def artwork_add(request):
    if request.method == "POST":
        type_key = request.POST.get("work_type", "book")
        work_form_class = _work_form_class(type_key)
        if work_form_class is None:
            return HttpResponseBadRequest("Неизвестный тип")
        post = request.POST.copy()
        for name in ("authors", "tags", "genres", "platforms"):
            ids = _parse_id_list(request, name)
            post.setlist(name, [str(item) for item in ids])
        work_form = work_form_class(post, request.FILES)
        if work_form.is_valid():
            try:
                with transaction.atomic():
                    work = work_form.save()
                    sync_work_relations(work, _parse_relations_payload(request))
            except ValidationError as error:
                message = " ".join(error.messages) if getattr(error, "messages", None) else str(error)
                return JsonResponse(
                    {"ok": False, "errors": {"__all__": [{"message": message}]}},
                    status=400,
                )
            meta = _progress_meta_for_work(work)
            return JsonResponse({
                "ok": True,
                "work_id": work.pk,
                "work_type": type_key,
                "title": work.title,
                "progressMax": meta["maximum"],
                "progressUnit": meta["unit"],
                "progressStep": meta["step"],
            })
        return JsonResponse(
            {"ok": False, "errors": work_form.errors.get_json_data()},
            status=400,
        )

    return render(request, "vor_archives/partials/artwork_add.html", {
        "add_opts": {
            "workType": "book",
            "saveUrl": reverse("vor_archives:artwork_add"),
            "searchUrl": reverse("vor_archives:artwork_search"),
            "previewUrl": reverse("vor_archives:artwork_preview"),
            "attachUrl": reverse("vor_archives:artwork_attach"),
            "listUrl": reverse("vor_archives:artwork_list"),
            "relationSearchUrl": reverse("vor_archives:artwork_relation_search"),
            "relationTypes": RELATION_TYPE_OPTIONS,
            "catalogs": _all_attr_catalogs(),
            "ageChoices": [
                {"value": value, "label": label}
                for value, label in AgeRatingChoices.choices
            ],
            "statusChoices": [
                {"value": value, "label": STATUS_LABELS_RU.get(value, label)}
                for value, label in UserWorkStatusChoices.choices
            ],
        },
    })


def _add_work_forms(bound_type=None, data=None, files=None):
    forms = {}
    for key, form_class in WORK_FORMS.items():
        if key == bound_type and data is not None:
            forms[f"{key}_form"] = form_class(data, files)
        else:
            forms[f"{key}_form"] = form_class()
    return forms


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_relation_search(request):
    results = search_works(
        request.GET.get("q") or "",
        exclude_type=request.GET.get("exclude_type"),
        exclude_id=request.GET.get("exclude_id"),
    )
    return JsonResponse({"results": results})


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
    return render(request, "vor_archives/partials/work_suggestions.html", {
        "works": works,
        "work_type": type_key,
        "query": query,
        "already_owned": already_owned,
    })


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_preview(request):
    type_key = request.GET.get("type") or request.GET.get("work_type") or "book"
    work_id = request.GET.get("work_id")
    if not work_id:
        return HttpResponseBadRequest("Не указано произведение")
    work = get_work(type_key, work_id)
    meta = _progress_meta_for_work(work)
    return render(request, "vor_archives/partials/work_preview_card.html", {
        "work": work,
        "work_type": type_key,
        "already": user_has_work(request.user, work),
        "progress_max": meta["maximum"],
        "progress_unit": meta["unit"],
        "progress_step": meta["step"],
    })


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_attach(request):
    type_key = request.POST.get("work_type")
    work_id = request.POST.get("work_id")
    if not type_key or not work_id:
        return HttpResponseBadRequest("Не указано произведение")
    work = get_work(type_key, work_id)
    if user_has_work(request.user, work):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "already"}, status=400)
        meta = _progress_meta_for_work(work)
        return render(request, "vor_archives/partials/work_preview_card.html", {
            "work": work,
            "work_type": type_key,
            "already": True,
            "progress_max": meta["maximum"],
            "progress_unit": meta["unit"],
            "progress_step": meta["step"],
        })
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
    attach_work(request.user, type_key, work_id, {
        "status": status,
        "rating": rating_value,
        "progress": progress_value,
    })
    if _wants_json(request):
        return JsonResponse({"ok": True})
    return _list_response(request, '{"vor:close-overlay": true}')


def _parse_ids(request):
    raw = request.GET.getlist("ids") or request.POST.getlist("ids")
    ids = []
    for value in raw:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids


@login_required(login_url=LOGIN_URL)
@require_GET
def artwork_delete_preview(request):
    ids = _parse_ids(request)
    user_works = list(
        UserWork.objects.filter(user=request.user, pk__in=ids).select_related(
            "work_content_type"
        )
    )
    prefetch_related_objects(user_works, "work")
    orphans = orphan_works(user_works)
    return render(request, "vor_archives/partials/delete_confirm.html", {
        "ids": [uw.pk for uw in user_works],
        "count": len(user_works),
        "orphan_titles": [work.title for work in orphans],
    })


@login_required(login_url=LOGIN_URL)
@require_POST
def artwork_delete(request):
    ids = _parse_ids(request)
    delete_user_works(request.user, ids)
    return _list_response(request, '{"vor:close-overlay": true}')


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
        item["detail_url"] = reverse("vor_archives:attr_detail", args=[kind, item["pk"]])
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
    item = _attach_item_urls("genres", {
        "key": genre_composite_id(type_key, obj.pk),
        "pk": obj.pk,
        "type_key": type_key,
        "type_label": meta["label"],
        "name": obj.name,
        "description": obj.description,
        "work_count": genre_work_count(obj, type_key),
        "has_text": True,
        "empty_text": "Нет описания",
    })
    return {
        "kind": "genres",
        "tab": get_attr_tab("genres"),
        "item": item,
        "is_staff": request.user.is_staff,
    }


def _simple_item_context(request, kind, obj):
    meta = SIMPLE_KINDS[kind]
    text_field = meta["text_field"]
    item = _attach_item_urls(kind, {
        "key": str(obj.pk),
        "pk": obj.pk,
        "name": obj.name,
        "description": getattr(obj, text_field) if text_field else "",
        "work_count": simple_work_count(obj, kind),
        "has_text": bool(text_field),
        "empty_text": meta.get("empty_text") or "Нет описания",
    })
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


def _form_context(kind, form, *, is_create, type_key=None, pk=None, type_label=None, lock_type=False):
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


def _attr_mutation_response(request, detail_template, detail_context, extra_trigger=None):
    response = render(request, detail_template, detail_context)
    triggers = {"vor:attr-list-refresh": True}
    if extra_trigger:
        triggers.update(extra_trigger)
    response["HX-Trigger"] = json.dumps(triggers)
    return response


@login_required(login_url=LOGIN_URL)
@require_GET
def attr_list(request, kind):
    return render(
        request,
        "vor_archives/partials/attr_list.html",
        _attr_list_context(request, kind),
    )


@login_required(login_url=LOGIN_URL)
@require_GET
def attr_empty(request, kind):
    return render(request, "vor_archives/partials/attr_empty.html", _empty_context(kind))


@login_required(login_url=LOGIN_URL)
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
        "vor_archives/partials/attr_detail.html",
        _simple_item_context(request, kind, obj),
    )


@login_required(login_url=LOGIN_URL)
@require_GET
def genre_detail(request, type_key, pk):
    if genre_type_meta(type_key) is None:
        return HttpResponseBadRequest("Неизвестный тип жанра")
    obj = get_genre(type_key, pk)
    if obj is None:
        raise Http404("Жанр не найден")
    return render(
        request,
        "vor_archives/partials/attr_detail.html",
        _genre_item_context(request, obj, type_key),
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def attr_new(request, kind):
    forbidden = _require_staff(request)
    if forbidden:
        return forbidden
    tab = _attr_tab_or_404(kind)
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
                    "vor_archives/partials/attr_detail.html",
                    _genre_item_context(request, obj, type_key),
                )
        else:
            form = GenreForm(initial_type=initial_type)
        return render(request, "vor_archives/partials/attr_form.html", _form_context(
            kind, form, is_create=True, type_label=genre_type_meta(initial_type)["label"],
        ))

    if kind not in SIMPLE_KINDS:
        raise Http404("Неизвестный тип атрибута")
    if request.method == "POST":
        form = AttrForm(request.POST, kind=kind)
        if form.is_valid():
            obj = form.save()
            return _attr_mutation_response(
                request,
                "vor_archives/partials/attr_detail.html",
                _simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind)
    return render(request, "vor_archives/partials/attr_form.html", _form_context(
        kind, form, is_create=True,
    ))


@login_required(login_url=LOGIN_URL)
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
                "vor_archives/partials/attr_detail.html",
                _simple_item_context(request, kind, obj),
            )
    else:
        form = AttrForm(kind=kind, instance=obj)
    return render(request, "vor_archives/partials/attr_form.html", _form_context(
        kind, form, is_create=False, pk=obj.pk,
    ))


@login_required(login_url=LOGIN_URL)
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
        form = GenreForm(request.POST, instance=obj, lock_type=True, initial_type=type_key)
        if form.is_valid():
            obj, saved_type = form.save()
            return _attr_mutation_response(
                request,
                "vor_archives/partials/attr_detail.html",
                _genre_item_context(request, obj, saved_type),
            )
    else:
        form = GenreForm(instance=obj, lock_type=True, initial_type=type_key)
    return render(request, "vor_archives/partials/attr_form.html", _form_context(
        "genres", form, is_create=False, type_key=type_key, pk=obj.pk,
        type_label=genre_type_meta(type_key)["label"], lock_type=True,
    ))


def _genre_delete_items(pairs):
    items = []
    for type_key, pk in pairs:
        obj = get_genre(type_key, pk)
        if obj is None:
            continue
        items.append({
            "key": genre_composite_id(type_key, pk),
            "type_key": type_key,
            "pk": pk,
            "name": obj.name,
            "type_label": genre_type_meta(type_key)["label"],
            "work_count": genre_work_count(obj, type_key),
            "obj": obj,
        })
    return items


def _simple_delete_items(kind, pks):
    items = []
    for pk in pks:
        obj = get_simple_attr(kind, pk)
        if obj is None:
            continue
        items.append({
            "key": str(pk),
            "pk": pk,
            "name": obj.name,
            "work_count": simple_work_count(obj, kind),
            "obj": obj,
        })
    return items


@login_required(login_url=LOGIN_URL)
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
    return render(request, "vor_archives/partials/attr_delete_confirm.html", {
        "kind": kind,
        "tab": tab,
        "items": items,
        "count": len(items),
        "delete_text": delete_text,
        "linked_count": sum(item["work_count"] for item in items),
        "delete_url": reverse("vor_archives:attr_delete", args=[kind]),
    })


@login_required(login_url=LOGIN_URL)
@require_POST
def attr_delete(request, kind):
    forbidden = _require_staff(request)
    if forbidden:
        return forbidden
    tab = _attr_tab_or_404(kind)
    if kind == "genres":
        items = _genre_delete_items(parse_genre_ids(request.POST.getlist("ids")))
    elif kind in SIMPLE_KINDS:
        items = _simple_delete_items(kind, parse_simple_ids(request.POST.getlist("ids")))
    else:
        raise Http404("Неизвестный тип атрибута")
    with transaction.atomic():
        for item in items:
            item["obj"].delete()
    return _attr_mutation_response(
        request,
        "vor_archives/partials/attr_empty.html",
        _empty_context(kind),
        extra_trigger={"vor:close-attr-modal": True},
    )
