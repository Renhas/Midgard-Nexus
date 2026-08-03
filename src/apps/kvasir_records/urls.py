from django.urls import path

from . import views

app_name = 'kvasir_records'

urlpatterns = [
    path('', views.index, name='index'),
]
