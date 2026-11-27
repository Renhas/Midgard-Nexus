import json

from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory

from config.context_processors import django_messages, toast_config
from config.toasts import attach_toast


def test_attach_toast_sets_hx_trigger_header():
    response = HttpResponse()
    attach_toast(
        response,
        "success",
        "Коллекция создана",
        message="Добавлена в боковую панель",
        action={"label": "Открыть", "event": "vor:select-collection", "detail": 5},
    )

    payload = json.loads(response["HX-Trigger"])
    assert payload == {
        "app:toast": {
            "level": "success",
            "title": "Коллекция создана",
            "message": "Добавлена в боковую панель",
            "action": {
                "label": "Открыть",
                "event": "vor:select-collection",
                "detail": 5,
            },
        }
    }


def test_attach_toast_merges_with_existing_json_triggers():
    response = HttpResponse()
    response["HX-Trigger"] = json.dumps(
        {"vor:reload-tree": True, "vor:close-modal": True}
    )

    attach_toast(response, "error", "Ошибка валидации", details="Trace", duration=0)

    payload = json.loads(response["HX-Trigger"])
    assert payload["vor:reload-tree"] is True
    assert payload["vor:close-modal"] is True
    assert payload["app:toast"] == {
        "level": "error",
        "title": "Ошибка валидации",
        "details": "Trace",
        "duration": 0,
    }


def test_attach_toast_preserves_plain_string_trigger():
    response = HttpResponse()
    response["HX-Trigger"] = "vor:reload-list"

    attach_toast(response, "info", "Обновлено")

    payload = json.loads(response["HX-Trigger"])
    assert payload["vor:reload-list"] is True
    assert payload["app:toast"] == {"level": "info", "title": "Обновлено"}


def test_toast_config_context_processor():
    request = RequestFactory().get("/")
    ctx = toast_config(request)
    assert ctx["toast_config"] == {
        "maxVisible": 5,
        "duration": 4000,
        "errorDuration": 7000,
    }


def test_django_messages_context_processor():
    request = RequestFactory().get("/")
    request.session = {}
    request._messages = FallbackStorage(request)
    messages.success(request, "Вход выполнен")
    messages.error(request, "Ошибка доступа")

    ctx = django_messages(request)
    assert ctx["django_messages"] == [
        {"level": "success", "message": "Вход выполнен"},
        {"level": "error", "message": "Ошибка доступа"},
    ]
