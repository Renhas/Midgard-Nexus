from apps.vor_archives.models import Person, Platform, Tag
from apps.vor_archives.registry import ATTRIBUTE_KIND_REGISTRY, WORK_TYPE_REGISTRY


def _build_tab(
    *,
    kind: str,
    noun_one: str,
    accusative_sg: str,
    genitive_pl: str,
    feminine: bool = False,
) -> dict[str, str]:
    meta = ATTRIBUTE_KIND_REGISTRY[kind]
    accusative_pl = meta.label.lower()
    new_adj = "Новая" if feminine else "Новый"
    deleted_verb = "удалена" if feminine else "удалён"
    return {
        "kind": meta.key,
        "label": meta.label,
        "icon": meta.icon,
        "search_placeholder": f"Поиск {genitive_pl}",
        "count_label": genitive_pl.capitalize(),
        "empty_prompt": f"Выберите {accusative_sg} из списка",
        "none_yet": f"{genitive_pl.capitalize()} пока нет",
        "create_title": f"{new_adj} {noun_one}",
        "delete_one": f"{noun_one.capitalize()} «{{name}}» будет {deleted_verb}.",
        "delete_many": f"Выбранные {accusative_pl} ({{count}}) будут удалены.",
    }


ATTR_TABS = [
    _build_tab(
        kind="tags",
        noun_one="тег",
        accusative_sg="тег",
        genitive_pl="тегов",
    ),
    _build_tab(
        kind="persons",
        noun_one="автор",
        accusative_sg="автора",
        genitive_pl="авторов",
    ),
    _build_tab(
        kind="genres",
        noun_one="жанр",
        accusative_sg="жанр",
        genitive_pl="жанров",
    ),
    _build_tab(
        kind="platforms",
        noun_one="платформа",
        accusative_sg="платформу",
        genitive_pl="платформ",
        feminine=True,
    ),
]

DEFAULT_KIND = "tags"

GENRE_TYPES = {
    key: {
        "model": meta.genre_model,
        "label": meta.label_plural,
        "count_field": key,
    }
    for key, meta in WORK_TYPE_REGISTRY.items()
}

SIMPLE_KINDS = {
    "tags": {
        "model": Tag,
        "name_label": "Название",
        "text_field": "description",
        "text_label": "Описание",
        "count_fields": ATTRIBUTE_KIND_REGISTRY["tags"].work_types,
        "unique_error": "Тег с таким названием уже существует",
        "empty_text": "Нет описания",
    },
    "persons": {
        "model": Person,
        "name_label": "Имя",
        "text_field": "bio",
        "text_label": "Биография",
        "count_fields": ATTRIBUTE_KIND_REGISTRY["persons"].work_types,
        "unique_error": "Автор с таким именем уже существует",
        "empty_text": "Нет биографии",
    },
    "platforms": {
        "model": Platform,
        "name_label": "Название",
        "text_field": None,
        "text_label": None,
        "count_fields": ATTRIBUTE_KIND_REGISTRY["platforms"].work_types,
        "unique_error": "Платформа с таким названием уже существует",
    },
}

ATTR_KIND_MAP = {tab["kind"]: tab for tab in ATTR_TABS}


def get_attr_tab(kind):
    return ATTR_KIND_MAP.get(kind)


def genre_type_meta(type_key):
    return GENRE_TYPES.get(type_key)
