from django.conf import settings
from django.shortcuts import render


def index(request):
    """Заглушка модуля «Кулинария»."""
    module = next(m for m in settings.MODULES if m["url_name"] == "kvasir_records")
    return render(
        request,
        "kvasir_records/wip.html",
        {
            "module_name": module["name"],
            "module_icon": module["icon"],
            "module_color": module["color"],
        },
    )
