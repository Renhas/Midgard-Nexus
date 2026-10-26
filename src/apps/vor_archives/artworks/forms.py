"""Forms for the artworks page."""

from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

from apps.vor_archives.constants import FilmTypeChoices, UserWorkStatusChoices
from apps.vor_archives.models import Book, Film, Game, UserWork

from .services.constants import WORK_MODELS
from .services.quick import QUICK_UPDATE_FIELDS


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
        fields = ("status", "rating", "progress", "is_hidden", "owned_platforms")
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
        widgets = {"owned_platforms": forms.SelectMultiple(attrs={"size": 4})}


WORK_FORMS = {
    "book": BookForm,
    "film": FilmForm,
    "game": GameForm,
}


class AttachWorkForm(forms.Form):
    """Validated payload for artwork_attach.

    Missing or "0" rating is normalized to None.
    Missing status defaults to PLANNING.
    Negative progress is clamped to 0.
    Out-of-range rating is rejected.
    """

    work_type = forms.ChoiceField(choices=[(key, key) for key in WORK_MODELS])
    work_id = forms.IntegerField()
    status = forms.ChoiceField(
        choices=UserWorkStatusChoices.choices,
        required=False,
    )
    rating = forms.IntegerField(required=False)
    progress = forms.DecimalField(required=False)

    def clean_status(self):
        return self.cleaned_data.get("status") or UserWorkStatusChoices.PLANNING

    def clean_rating(self):
        value = self.cleaned_data.get("rating")
        if value is None or value == 0:
            return None
        if value < 1 or value > 10:
            raise forms.ValidationError("Некорректный рейтинг")
        return value

    def clean_progress(self):
        value = self.cleaned_data.get("progress")
        if value is None or value < 0:
            return Decimal("0")
        return value


class QuickUpdateForm(forms.Form):
    """Validated payload for artwork_quick.

    `value` is polymorphic: parsing is dispatched per field.
    Unknown fields and invalid values produce form errors, not exceptions.
    """

    FIELD_CHOICES = [(key, spec.label) for key, spec in QUICK_UPDATE_FIELDS.items()]
    field = forms.ChoiceField(choices=FIELD_CHOICES)
    value = forms.CharField(required=False)

    def clean(self):
        cleaned = super().clean()
        field = cleaned.get("field")
        if not field:
            return cleaned
        raw = cleaned.get("value", "")
        try:
            cleaned["value"] = self._parse_value(field, raw)
        except ValidationError as exc:
            self.add_error("value", exc)
        return cleaned

    def _parse_value(self, field, raw):
        parser = getattr(self, f"_parse_{field}")
        return parser(raw)

    def _parse_status(self, raw):
        if raw not in {choice[0] for choice in UserWorkStatusChoices.choices}:
            raise ValidationError("Некорректный статус")
        return raw

    def _parse_progress(self, raw):
        try:
            value = Decimal(raw)
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Некорректный прогресс")
        return max(value, Decimal("0"))

    def _parse_rating(self, raw):
        if raw in ("", "0"):
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ValidationError("Некорректный рейтинг")
        if value < 1 or value > 10:
            raise ValidationError("Некорректный рейтинг")
        return value

    def _parse_is_hidden(self, raw):
        return raw in ("1", "true", "True")

    def _parse_times_completed(self, raw):
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ValidationError("Некорректное число завершений")
        return max(value, 0)

    def _parse_owned_platform(self, raw):
        try:
            return int(raw)
        except (TypeError, ValueError):
            raise ValidationError("Некорректная платформа")
