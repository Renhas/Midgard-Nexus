from django.urls import path

from . import views

app_name = "vor_archives"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("attributes/", views.attributes, name="attributes"),
    path("attributes/genres/list/", views.genre_list, name="genre_list"),
    path("attributes/genres/empty/", views.genre_empty, name="genre_empty"),
    path("attributes/genres/new/", views.genre_new, name="genre_new"),
    path("attributes/genres/delete/preview/", views.genre_delete_preview, name="genre_delete_preview"),
    path("attributes/genres/delete/", views.genre_delete, name="genre_delete"),
    path("attributes/genres/<str:type_key>/<int:pk>/edit/", views.genre_edit, name="genre_edit"),
    path("attributes/genres/<str:type_key>/<int:pk>/", views.genre_detail, name="genre_detail"),
    path("attributes/<str:kind>/", views.attributes_kind, name="attributes_kind"),
    path("artworks/", views.artwork_list, name="artwork_list"),
    path("artworks/new/", views.artwork_add, name="artwork_add"),
    path("artworks/search/", views.artwork_search, name="artwork_search"),
    path("artworks/relation-search/", views.artwork_relation_search, name="artwork_relation_search"),
    path("artworks/preview/", views.artwork_preview, name="artwork_preview"),
    path("artworks/attach/", views.artwork_attach, name="artwork_attach"),
    path("artworks/delete/preview/", views.artwork_delete_preview, name="artwork_delete_preview"),
    path("artworks/delete/", views.artwork_delete, name="artwork_delete"),
    path("artworks/<int:uw_id>/quick/", views.artwork_quick, name="artwork_quick"),
    path("artworks/<int:uw_id>/", views.artwork_detail, name="artwork_detail"),
    path("works/<str:type_key>/<int:work_id>/", views.artwork_work, name="artwork_work"),
]
