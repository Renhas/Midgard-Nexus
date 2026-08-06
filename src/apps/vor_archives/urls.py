from django.urls import path

from . import views

app_name = 'vor_archives'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attributes/', views.attributes, name='attributes'),
]
