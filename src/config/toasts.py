import json


def _parse_hx_triggers(raw_header: str | None) -> dict:
    if not raw_header:
        return {}
    try:
        parsed = json.loads(raw_header)
        return parsed if isinstance(parsed, dict) else {str(parsed): True}
    except (ValueError, TypeError):
        return {raw_header: True}


def attach_toast(
    response,
    level: str,
    title: str,
    *,
    message: str = "",
    action: dict | None = None,
    details: str = "",
    duration: int | None = None,
):
    """Добавляет событие app:toast в заголовок HX-Trigger HTTP-ответа."""
    optional_fields = {
        "message": message,
        "action": action,
        "details": details,
        "duration": duration,
    }
    payload = {
        "level": level,
        "title": title,
        **{
            key: value
            for key, value in optional_fields.items()
            if value not in ("", None)
        },
    }

    triggers = _parse_hx_triggers(response.headers.get("HX-Trigger"))
    triggers["app:toast"] = payload
    response["HX-Trigger"] = json.dumps(triggers)
    return response
