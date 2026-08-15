from django.urls import path

from . import views

app_name = "vor_archives"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("attributes/", views.attributes, name="attributes"),
    path("artworks/", views.artwork_list, name="artwork_list"),
    path("artworks/new/", views.artwork_add, name="artwork_add"),
    path("artworks/search/", views.artwork_search, name="artwork_search"),
    path("artworks/preview/", views.artwork_preview, name="artwork_preview"),
    path("artworks/attach/", views.artwork_attach, name="artwork_attach"),
    path("artworks/delete/preview/", views.artwork_delete_preview, name="artwork_delete_preview"),
    path("artworks/delete/", views.artwork_delete, name="artwork_delete"),
    path("artworks/<int:uw_id>/", views.artwork_detail, name="artwork_detail"),
]
