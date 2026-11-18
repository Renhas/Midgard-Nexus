from apps.vor_archives.models import (
    BookGenre,
    FilmGenre,
    GameGenre,
    Person,
    Platform,
    Tag,
)

ATTR_TABS = [
    {
        "kind": "tags",
        "label": "Теги",
        "icon": "bi bi-tag",
        "search_placeholder": "Поиск тега",
        "count_label": "Тегов",
        "empty_prompt": "Выберите тег из списка",
        "none_yet": "Тегов пока нет",
        "create_title": "Новый тег",
        "noun_one": "тег",
        "noun_many": "теги",
        "delete_one": "Тег «{name}» будет удалён.",
        "delete_many": "Выбранные теги ({count}) будут удалены.",
    },
    {
        "kind": "persons",
        "label": "Авторы",
        "icon": "bi bi-person",
        "search_placeholder": "Поиск автора",
        "count_label": "Авторов",
        "empty_prompt": "Выберите автора из списка",
        "none_yet": "Авторов пока нет",
        "create_title": "Новый автор",
        "noun_one": "автор",
        "noun_many": "авторы",
        "delete_one": "Автор «{name}» будет удалён.",
        "delete_many": "Выбранные авторы ({count}) будут удалены.",
    },
    {
        "kind": "genres",
        "label": "Жанры",
        "icon": "icon-drama",
        "search_placeholder": "Поиск жанра",
        "count_label": "Жанров",
        "empty_prompt": "Выберите жанр из списка",
        "none_yet": "Жанров пока нет",
        "create_title": "Новый жанр",
        "noun_one": "жанр",
        "noun_many": "жанры",
        "delete_one": "Жанр «{name}» будет удалён.",
        "delete_many": "Выбранные жанры ({count}) будут удалены.",
    },
    {
        "kind": "platforms",
        "label": "Платформы",
        "icon": "bi bi-controller",
        "search_placeholder": "Поиск платформы",
        "count_label": "Платформ",
        "empty_prompt": "Выберите платформу из списка",
        "none_yet": "Платформ пока нет",
        "create_title": "Новая платформа",
        "noun_one": "платформа",
        "noun_many": "платформы",
        "delete_one": "Платформа «{name}» будет удалена.",
        "delete_many": "Выбранные платформы ({count}) будут удалены.",
    },
]

DEFAULT_KIND = "tags"

GENRE_TYPES = {
    "book": {"model": BookGenre, "label": "Книги", "count_field": "book"},
    "film": {"model": FilmGenre, "label": "Фильмы", "count_field": "film"},
    "game": {"model": GameGenre, "label": "Игры", "count_field": "game"},
}

SIMPLE_KINDS = {
    "tags": {
        "model": Tag,
        "name_label": "Название",
        "text_field": "description",
        "text_label": "Описание",
        "count_fields": ("book", "film", "game"),
        "unique_error": "Тег с таким названием уже существует",
        "empty_text": "Нет описания",
    },
    "persons": {
        "model": Person,
        "name_label": "Имя",
        "text_field": "bio",
        "text_label": "Биография",
        "count_fields": ("book", "film", "game"),
        "unique_error": "Автор с таким именем уже существует",
        "empty_text": "Нет биографии",
    },
    "platforms": {
        "model": Platform,
        "name_label": "Название",
        "text_field": None,
        "text_label": None,
        "count_fields": ("game",),
        "unique_error": "Платформа с таким названием уже существует",
    },
}

ATTR_KIND_MAP = {tab["kind"]: tab for tab in ATTR_TABS}


def get_attr_tab(kind):
    return ATTR_KIND_MAP.get(kind)


def genre_type_meta(type_key):
    return GENRE_TYPES.get(type_key)
