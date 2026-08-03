from django.shortcuts import render

# Create your views here.

def profile(request):
    """Страница профиля пользователя."""
    return render(request, 'users/profile.html')
