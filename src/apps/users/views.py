from django.shortcuts import render, redirect
from django.contrib.auth import login

from .forms import SignUpForm


def profile(request):
    """Страница профиля пользователя."""
    return render(request, 'users/profile.html')


def signup(request):
    """Страница регистрации пользователя."""
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "users/auth/signup.html", {"form": form})
