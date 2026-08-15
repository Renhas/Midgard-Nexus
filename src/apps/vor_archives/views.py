from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import prefetch_related_objects
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import AgeRatingChoices, FilmTypeChoices, UserWorkStatusChoices
from .forms import WORK_FORMS, UserWorkEditForm, UserWorkForm
from .templatetags.vor_archives_extras import get_progress_info
from .models import BookGenre, Collection, FilmGenre, GameGenre, Platform, Tag, UserWork
from .services import (
    WORK_MODELS,
    attach_work,
    create_work_and_attach,
    delete_user_works,
    get_user_work,
    get_work,
    orphan_works,
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
    """Страница атрибутов модуля «Библиотека»."""
    module = _module_context()
    return render(request, "vor_archives/attributes.html", {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_color": module["color"],
        "active_section": "attributes",
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


def _detail_context(request, work, user_work=None, work_form=None, user_work_form=None, editing=False, global_edit=False):
    type_key = work_type_key(work)
    owned = user_work is not None
    progress_meta = (get_progress_info(user_work) or {}) if owned else {}
    owned_platform_ids = []
    if owned:
        owned_platform_ids = list(user_work.owned_platforms.values_list("pk", flat=True))
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
        "status_choices": UserWorkStatusChoices.choices,
        "work_relations": work_relation_items(work),
        "overlay_opts": {
            "editing": editing,
            "globalEdit": global_edit,
            "owned": owned,
            "filmType": getattr(work, "film_type", None) or "movie",
            "status": user_work.status if owned else "planning",
            "statusChoices": [
                {"value": value, "label": label}
                for value, label in UserWorkStatusChoices.choices
            ],
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
        global_edit = request.POST.get("global_edit") == "1" and request.user.is_staff
        user_work_form = (
            UserWorkEditForm(request.POST, instance=user_work)
            if user_work is not None
            else None
        )
        if global_edit:
            work_form = work_form_class(request.POST, request.FILES, instance=work)
            user_ok = user_work_form is None or user_work_form.is_valid()
            if user_ok and work_form.is_valid():
                if user_work_form is not None:
                    user_work_form.save()
                work_form.save()
                return _list_response(request, '{"vor:close-overlay": true}')
        elif user_work_form is not None:
            work_form = work_form_class(instance=work)
            if user_work_form.is_valid():
                user_work_form.save()
                return _list_response(request, '{"vor:close-overlay": true}')
        else:
            return HttpResponseBadRequest("Недостаточно прав")
        return render(
            request,
            "vor_archives/partials/artwork_overlay.html",
            _detail_context(
                request, work, user_work, work_form, user_work_form,
                editing=True, global_edit=global_edit,
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
        forms = _add_work_forms(type_key, request.POST, request.FILES)
        work_form = forms[f"{type_key}_form"]
        user_work_form = UserWorkForm(request.POST)
        title_value = request.POST.get("title", "")
        if user_has_work_title(request.user, type_key, title_value):
            work_form.add_error(
                "title",
                "Произведение с таким названием уже есть в вашем списке",
            )
        if work_form.is_valid() and user_work_form.is_valid():
            work = work_form.save()
            create_work_and_attach(request.user, work, user_work_form)
            return _list_response(request, '{"vor:close-overlay": true}')
        return render(request, "vor_archives/partials/artwork_add.html", {
            **forms,
            "work_form": work_form,
            "work_type": type_key,
            "user_work_form": user_work_form,
            "title_value": title_value,
            "create_errors": True,
            "progress_unit": _progress_unit(type_key=type_key),
        })

    forms = _add_work_forms()
    return render(request, "vor_archives/partials/artwork_add.html", {
        **forms,
        "work_form": forms["book_form"],
        "work_type": "book",
        "user_work_form": UserWorkForm(),
        "progress_unit": _progress_unit(type_key="book"),
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
    return render(request, "vor_archives/partials/work_preview_card.html", {
        "work": work,
        "work_type": type_key,
        "already": user_has_work(request.user, work),
        "user_work_form": UserWorkForm(),
        "progress_unit": _progress_unit(work),
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
        return render(request, "vor_archives/partials/work_preview_card.html", {
            "work": work,
            "work_type": type_key,
            "already": True,
            "user_work_form": UserWorkForm(),
            "progress_unit": _progress_unit(work),
        })
    user_work_form = UserWorkForm(request.POST)
    if not user_work_form.is_valid():
        return render(request, "vor_archives/partials/work_preview_card.html", {
            "work": work,
            "work_type": type_key,
            "already": False,
            "attaching": True,
            "user_work_form": user_work_form,
            "progress_unit": _progress_unit(work),
        })
    attach_work(request.user, type_key, work_id, user_work_form.cleaned_data)
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
