import json


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
    payload: dict = {
        "level": level,
        "title": title,
    }
    if message:
        payload["message"] = message
    if action:
        payload["action"] = action
    if details:
        payload["details"] = details
    if duration is not None:
        payload["duration"] = duration

    existing_raw = response.headers.get("HX-Trigger")
    if existing_raw:
        try:
            triggers = json.loads(existing_raw)
            if not isinstance(triggers, dict):
                triggers = {str(triggers): True}
        except (ValueError, TypeError):
            triggers = {existing_raw: True}
    else:
        triggers = {}

    triggers["app:toast"] = payload
    response["HX-Trigger"] = json.dumps(triggers)
    return response
