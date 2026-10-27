import json

from django.http import HttpResponse

from apps.vor_archives.artworks.forms import WORK_FORMS, ArtworkListFilterForm
from apps.vor_archives.progress import work_progress


def progress_meta_for_work(work):
    meta = work_progress(work)
    return {"maximum": meta.maximum, "unit": meta.unit, "step": meta.step}


def wants_json(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def artwork_list_params(request):
    form = ArtworkListFilterForm(request.GET)
    if not form.is_valid():
        form = ArtworkListFilterForm({})
    return form.to_service_params()


def list_response(request, trigger=None):
    payload = {"vor:reload-list": True}
    if trigger:
        extra = json.loads(trigger) if isinstance(trigger, str) else dict(trigger)
        payload.update(extra)
    response = HttpResponse()
    response["HX-Trigger"] = json.dumps(payload)
    return response


def get_work_form_class(type_key):
    try:
        return WORK_FORMS[type_key]
    except KeyError:
        return None
