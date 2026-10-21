def optional_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_ids(request):
    raw = request.GET.getlist("ids") or request.POST.getlist("ids")
    ids = []
    for value in raw:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids
