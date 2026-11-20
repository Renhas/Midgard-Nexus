"""Tests for AttrForm in apps.vor_archives.attributes.forms."""

import pytest

from apps.vor_archives.attributes.forms import AttrForm
from apps.vor_archives.models import Person, Platform, Tag
from apps.vor_archives.tests.factories import (
    PersonFactory,
    PlatformFactory,
    TagFactory,
)

pytestmark = pytest.mark.django_db


# ─── Инициализация и поля ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "kind,expected_fields,name_label,text_label",
    [
        pytest.param("tags", ["name", "text"], "Название", "Описание", id="tags"),
        pytest.param("persons", ["name", "text"], "Имя", "Биография", id="persons"),
        pytest.param("platforms", ["name"], "Название", None, id="platforms-no-text"),
    ],
)
def test_attr_form_fields_and_labels(kind, expected_fields, name_label, text_label):
    form = AttrForm(kind=kind)
    assert list(form.fields) == expected_fields
    assert form.fields["name"].label == name_label
    assert form.fields["name"].widget.attrs["class"] == "form-control"
    if text_label is not None:
        assert form.fields["text"].label == text_label
        assert form.fields["text"].widget.attrs["class"] == "form-control"


def test_attr_form_initial_from_instance():
    person = PersonFactory(name="Tolkien", bio="Writer")
    form = AttrForm(kind="persons", instance=person)
    assert form.initial == {"name": "Tolkien", "text": "Writer"}

    platform = PlatformFactory(name="PC")
    platform_form = AttrForm(kind="platforms", instance=platform)
    assert platform_form.initial == {"name": "PC"}


# ─── Валидация clean_name ───────────────────────────────────────────────────


@pytest.mark.parametrize("kind", ["tags", "persons", "platforms"])
@pytest.mark.parametrize("raw_name", ["", "   "])
def test_attr_form_rejects_blank_name(kind, raw_name):
    form = AttrForm(data={"name": raw_name}, kind=kind)
    assert not form.is_valid()
    assert form.errors["name"] == ["Обязательное поле."]


def test_attr_form_strips_whitespace_on_save():
    form = AttrForm(data={"name": "  Sci-Fi  ", "text": "Space"}, kind="tags")
    assert form.is_valid()
    obj = form.save()
    assert obj.name == "Sci-Fi"
    assert obj.description == "Space"


@pytest.mark.parametrize(
    "kind,factory_cls,duplicate_input,expected_error",
    [
        pytest.param(
            "tags",
            lambda: TagFactory(name="Fantasy"),
            "fantasy",
            "Тег с таким названием уже существует",
            id="tags-iexact",
        ),
        pytest.param(
            "persons",
            lambda: PersonFactory(name="King"),
            "  KING  ",
            "Автор с таким именем уже существует",
            id="persons-iexact-trimmed",
        ),
        pytest.param(
            "platforms",
            lambda: PlatformFactory(name="Steam"),
            "STEAM",
            "Платформа с таким названием уже существует",
            id="platforms-iexact",
        ),
    ],
)
def test_attr_form_unique_name_case_insensitive(
    kind, factory_cls, duplicate_input, expected_error
):
    factory_cls()
    form = AttrForm(data={"name": duplicate_input}, kind=kind)
    assert not form.is_valid()
    assert form.errors["name"] == [expected_error]


def test_attr_form_edit_allows_same_name_for_self_but_rejects_other():
    t1 = TagFactory(name="Alpha")
    TagFactory(name="Beta")

    same_form = AttrForm(
        data={"name": "alpha", "text": "Updated"}, kind="tags", instance=t1
    )
    assert same_form.is_valid()
    saved = same_form.save()
    assert saved.pk == t1.pk
    assert saved.name == "alpha"
    assert saved.description == "Updated"

    conflict_form = AttrForm(data={"name": "BETA"}, kind="tags", instance=t1)
    assert not conflict_form.is_valid()
    assert conflict_form.errors["name"] == ["Тег с таким названием уже существует"]


# ─── save() ─────────────────────────────────────────────────────────────────


def test_attr_form_save_create_and_update():
    create_form = AttrForm(data={"name": "GoG"}, kind="platforms")
    assert create_form.is_valid()
    created = create_form.save()
    assert isinstance(created, Platform)
    assert created.pk is not None
    assert created.name == "GoG"

    edit_form = AttrForm(
        data={"name": "GOG Galaxy"}, kind="platforms", instance=created
    )
    assert edit_form.is_valid()
    updated = edit_form.save()
    assert updated.pk == created.pk
    assert updated.name == "GOG Galaxy"
    assert Platform.objects.count() == 1
