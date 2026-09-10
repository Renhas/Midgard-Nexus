from django.conf import settings
from django.shortcuts import render


def index(request):
    """Заглушка модуля «Финансы»."""
    module = next(m for m in settings.MODULES if m["url_name"] == "fafnir_cave")
    return render(
        request,
        "fafnir_cave/wip.html",
        {
            "module_name": module["name"],
            "module_icon": module["icon"],
            "module_color": module["color"],
        },
    )
