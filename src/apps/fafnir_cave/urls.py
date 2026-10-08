from django.urls import path

from . import views

app_name = "fafnir_cave"

urlpatterns = [
    path("", views.index, name="index"),
]
