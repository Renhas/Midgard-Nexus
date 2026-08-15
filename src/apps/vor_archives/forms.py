from django import forms

from .constants import FilmTypeChoices
from .models import Book, Film, Game, UserWork


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class UserWorkForm(StyledModelForm):
    class Meta:
        model = UserWork
        fields = (
            "status",
            "rating",
            "progress",
            "is_hidden",
            "owned_platforms",
        )
        labels = {
            "status": "Статус",
            "rating": "Рейтинг",
            "progress": "Прогресс",
            "is_hidden": "Скрыто",
            "owned_platforms": "Платформы",
        }
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 10}),
            "progress": forms.NumberInput(attrs={"min": 0, "step": "0.1"}),
            "owned_platforms": forms.SelectMultiple(attrs={"size": 4}),
        }


class WorkBaseForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "release_date" in self.fields:
            self.fields["release_date"].input_formats = ["%Y-%m-%d"]

    class Meta:
        fields = (
            "title",
            "release_date",
            "description",
            "cover",
            "authors",
            "tags",
            "external_link",
            "age_rating",
        )
        labels = {
            "title": "Название",
            "release_date": "Дата выхода",
            "description": "Описание",
            "cover": "Обложка",
            "authors": "Авторы",
            "tags": "Теги",
            "external_link": "Ссылка",
            "age_rating": "Возрастной рейтинг",
        }
        widgets = {
            "release_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "authors": forms.SelectMultiple(attrs={"size": 4}),
            "tags": forms.SelectMultiple(attrs={"size": 4}),
        }


class BookForm(WorkBaseForm):
    class Meta(WorkBaseForm.Meta):
        model = Book
        fields = WorkBaseForm.Meta.fields + ("pages", "genres")
        labels = {
            **WorkBaseForm.Meta.labels,
            "pages": "Страниц",
            "genres": "Жанры",
        }
        widgets = {
            **WorkBaseForm.Meta.widgets,
            "genres": forms.SelectMultiple(attrs={"size": 4}),
        }


class FilmForm(WorkBaseForm):
    class Meta(WorkBaseForm.Meta):
        model = Film
        fields = WorkBaseForm.Meta.fields + (
            "duration_minutes",
            "film_type",
            "episode_count",
            "genres",
        )
        labels = {
            **WorkBaseForm.Meta.labels,
            "duration_minutes": "Длительность (мин.)",
            "film_type": "Тип фильма",
            "episode_count": "Эпизодов",
            "genres": "Жанры",
        }
        widgets = {
            **WorkBaseForm.Meta.widgets,
            "film_type": forms.Select(attrs={"x-model": "filmType"}),
            "genres": forms.SelectMultiple(attrs={"size": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("film_type") == FilmTypeChoices.MOVIE:
            cleaned["episode_count"] = None
        return cleaned


class GameForm(WorkBaseForm):
    class Meta(WorkBaseForm.Meta):
        model = Game
        fields = WorkBaseForm.Meta.fields + ("platforms", "genres")
        labels = {
            **WorkBaseForm.Meta.labels,
            "platforms": "Платформы",
            "genres": "Жанры",
        }
        widgets = {
            **WorkBaseForm.Meta.widgets,
            "platforms": forms.SelectMultiple(attrs={"size": 4}),
            "genres": forms.SelectMultiple(attrs={"size": 4}),
        }


class UserWorkEditForm(StyledModelForm):
    class Meta:
        model = UserWork
        fields = ("owned_platforms",)
        labels = {"owned_platforms": "Платформы"}
        widgets = {
            "owned_platforms": forms.SelectMultiple(attrs={"size": 4}),
        }


WORK_FORMS = {
    "book": BookForm,
    "film": FilmForm,
    "game": GameForm,
}
