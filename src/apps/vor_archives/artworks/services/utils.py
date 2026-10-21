def work_key(obj):
    return (obj.work_content_type_id, obj.work_object_id)


def relation_cover_url(work):
    cover = getattr(work, "cover", None)
    if not cover:
        return ""
    try:
        return cover.url
    except ValueError:
        return ""


def _as_str_set(values):
    return {str(value) for value in (values or [])}


def is_partial(selected, all_values):
    if not all_values:
        return False
    return _as_str_set(selected) != _as_str_set(all_values)


def item_ids(items):
    return {item.pk for item in items}
