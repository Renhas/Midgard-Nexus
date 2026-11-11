from django.template import Context, Template


def test_render_filter_accordion_simple():
    template = Template(
        "{% load vor_archives_extras %}{% render_filter_accordion section %}"
    )
    section = {
        "title": "Статус",
        "options": [{"value": "1", "label": "Активен"}],
        "name": "status",
    }
    html = template.render(Context({"section": section}))
    assert "Статус" in html
    assert 'name="status"' in html
    assert "Активен" in html
    assert "Поиск" not in html


def test_render_filter_accordion_searchable():
    template = Template(
        "{% load vor_archives_extras %}{% render_filter_accordion section %}"
    )
    section = {
        "title": "Теги",
        "options": [{"value": "1", "label": "Фантастика"}],
        "name": "tags",
        "searchable": True,
    }
    html = template.render(Context({"section": section}))
    assert "Теги" in html
    assert "Поиск" in html
    assert "Снять все" in html


def test_render_filter_accordion_nested():
    template = Template(
        "{% load vor_archives_extras %}{% render_filter_accordion section %}"
    )
    section = {
        "title": "Жанры",
        "nested": [
            {
                "title": "Книги",
                "options": [{"value": "1", "label": "Роман"}],
                "name": "genre_book",
                "show_condition": "true",
            }
        ],
    }
    html = template.render(Context({"section": section}))
    assert "Жанры" in html
    assert "Книги" in html
    assert "Роман" in html
