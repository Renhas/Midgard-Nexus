from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpForm(UserCreationForm):
    username = forms.CharField(label="Логин")

    class Meta:  # type: ignore
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "username"
        ].help_text = (
            "Максимум 150 символов. Допускаются буквы, цифры и символы @/./+/-/_"
        )
        self.fields[
            "password1"
        ].help_text = "Минимум 8 символов, не может состоять только из цифр"
        self.fields["password2"].help_text = ""
