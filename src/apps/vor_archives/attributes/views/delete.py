from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from ..services import delete_attrs, resolve_delete_items
from .utils import (
    attr_mutation_response,
    attr_tab_or_404,
    empty_context,
    staff_required,
)


@login_required
@staff_required
@require_GET
def attr_delete_preview(request, kind):
    tab = attr_tab_or_404(kind)
    try:
        items = resolve_delete_items(kind, request.GET.getlist("ids"))
    except ValueError:
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
            "delete_url": reverse("vor_archives:attributes:delete", args=[kind]),
        },
    )


@login_required
@staff_required
@require_POST
def attr_delete(request, kind):
    attr_tab_or_404(kind)
    try:
        deleted_count = delete_attrs(kind, request.POST.getlist("ids"))
    except ValueError:
        raise Http404("Неизвестный тип атрибута")
    return attr_mutation_response(
        request,
        "vor_archives/partials/attributes/attr_empty.html",
        empty_context(kind),
        extra_trigger={
            "vor:close-attr-modal": True,
            "vor:attr-deleted": {"count": deleted_count},
        },
    )
