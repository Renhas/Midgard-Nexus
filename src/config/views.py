from django.shortcuts import render


def home(request):
    """Главная страница с карточками модулей."""
    return render(request, 'home.html')
