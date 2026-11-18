from apps.vor_archives.utils import parse_int_list


def parse_ids(request):
    raw = request.GET.getlist("ids") or request.POST.getlist("ids")
    return parse_int_list(raw)


def parse_id_list(request, name):
    return parse_int_list(request.POST.getlist(name), comma_separated=True)
