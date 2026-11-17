from django import forms

from .attr_catalog import GENRE_TYPES, SIMPLE_KINDS, genre_type_key


class GenreForm(forms.Form):
    TYPE_CHOICES = tuple((key, meta["label"]) for key, meta in GENRE_TYPES.items())

    type_key = forms.ChoiceField(choices=TYPE_CHOICES, label="Тип")
    name = forms.CharField(max_length=255, label="Название")
    description = forms.CharField(
        required=False,
        label="Описание",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def __init__(
        self, *args, instance=None, lock_type=False, initial_type=None, **kwargs
    ):
        self.instance = instance
        self.lock_type = lock_type
        self.fixed_type = initial_type
        if instance is not None and self.fixed_type is None:
            self.fixed_type = genre_type_key(instance)
        initial = kwargs.pop("initial", None) or {}
        if instance is not None:
            initial.setdefault("name", instance.name)
            initial.setdefault("description", instance.description)
        if self.fixed_type:
            initial.setdefault("type_key", self.fixed_type)
        super().__init__(*args, initial=initial, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
        if lock_type:
            self.fields["type_key"].disabled = True
            self.fields["type_key"].required = False

    def _resolved_type(self):
        if self.lock_type and self.fixed_type:
            return self.fixed_type
        return self.cleaned_data.get("type_key") or self.fixed_type

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Введите название")
        type_key = self.data.get("type_key") or self.fixed_type
        meta = GENRE_TYPES.get(type_key)
        if meta is None:
            return name
        qs = meta["model"].objects.filter(name__iexact=name)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Жанр с таким названием уже существует")
        return name

    def save(self):
        type_key = self._resolved_type()
        model = GENRE_TYPES[type_key]["model"]
        name = self.cleaned_data["name"]
        description = self.cleaned_data.get("description") or ""
        if self.instance is None:
            self.instance = model(name=name, description=description)
        else:
            self.instance.name = name
            self.instance.description = description
        self.instance.save()
        return self.instance, type_key


class AttrForm(forms.Form):
    name = forms.CharField(max_length=255, label="Название")
    text = forms.CharField(
        required=False,
        label="Описание",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def __init__(self, *args, kind=None, instance=None, **kwargs):
        self.kind = kind
        self.meta = SIMPLE_KINDS[kind]
        self.instance = instance
        initial = kwargs.pop("initial", None) or {}
        if instance is not None:
            initial.setdefault("name", instance.name)
            text_field = self.meta["text_field"]
            if text_field:
                initial.setdefault("text", getattr(instance, text_field) or "")
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["name"].label = self.meta["name_label"]
        if self.meta["text_field"]:
            self.fields["text"].label = self.meta["text_label"]
        else:
            del self.fields["text"]
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError(f"Введите {self.meta['name_label'].lower()}")
        qs = self.meta["model"].objects.filter(name__iexact=name)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(self.meta["unique_error"])
        return name

    def save(self):
        model = self.meta["model"]
        name = self.cleaned_data["name"]
        text_field = self.meta["text_field"]
        text = (self.cleaned_data.get("text") or "") if text_field else ""
        if self.instance is None:
            kwargs = {"name": name}
            if text_field:
                kwargs[text_field] = text
            self.instance = model(**kwargs)
        else:
            self.instance.name = name
            if text_field:
                setattr(self.instance, text_field, text)
        self.instance.save()
        return self.instance
