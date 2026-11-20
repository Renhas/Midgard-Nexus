from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.vor_archives.utils import module_base_context
from ..catalog import ATTR_TABS, DEFAULT_KIND, get_attr_tab


@login_required
def attributes(request):
    """Страница атрибутов — редирект на первую готовую вкладку."""
    return redirect("vor_archives:attributes:kind", kind=DEFAULT_KIND)


@login_required
def attributes_kind(request, kind):
    """Оболочка страницы атрибутов для выбранной вкладки."""
    tab = get_attr_tab(kind)
    if tab is None:
        raise Http404("Неизвестный тип атрибута")
    return render(
        request,
        "vor_archives/attributes.html",
        {
            **module_base_context("attributes", hide_right=True),
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
