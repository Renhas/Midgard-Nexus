def parse_int_list(raw_values, *, comma_separated=False):
    """Parse raw string values into a list of ints.

    Empty and non-numeric entries are skipped silently. When
    comma_separated is True, each raw value is split on commas first,
    allowing both repeated keys and comma-separated lists to be used in
    the same field.
    """
    result = []
    for raw in raw_values:
        parts = str(raw).split(",") if comma_separated else [str(raw)]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                result.append(int(part))
            except ValueError:
                continue
    return result


def parse_ids(request):
    raw = request.GET.getlist("ids") or request.POST.getlist("ids")
    return parse_int_list(raw)


def parse_id_list(request, name):
    return parse_int_list(request.POST.getlist(name), comma_separated=True)
