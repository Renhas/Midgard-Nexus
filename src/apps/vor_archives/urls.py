from django.urls import path

from . import views

app_name = "vor_archives"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("attributes/", views.attributes, name="attributes"),
    path("attributes/<str:kind>/list/", views.attr_list, name="attr_list"),
    path("attributes/<str:kind>/empty/", views.attr_empty, name="attr_empty"),
    path("attributes/<str:kind>/new/", views.attr_new, name="attr_new"),
    path("attributes/<str:kind>/delete/preview/", views.attr_delete_preview, name="attr_delete_preview"),
    path("attributes/<str:kind>/delete/", views.attr_delete, name="attr_delete"),
    path("attributes/genres/<str:type_key>/<int:pk>/edit/", views.genre_edit, name="genre_edit"),
    path("attributes/genres/<str:type_key>/<int:pk>/", views.genre_detail, name="genre_detail"),
    path("attributes/<str:kind>/<int:pk>/edit/", views.attr_edit, name="attr_edit"),
    path("attributes/<str:kind>/<int:pk>/", views.attr_detail, name="attr_detail"),
    path("attributes/<str:kind>/", views.attributes_kind, name="attributes_kind"),
    path("artworks/", views.artwork_list, name="artwork_list"),
    path("artworks/new/", views.artwork_add, name="artwork_add"),
    path("artworks/search/", views.artwork_search, name="artwork_search"),
    path("artworks/library-search/", views.artwork_library_search, name="artwork_library_search"),
    path("artworks/reorder/", views.artwork_reorder, name="artwork_reorder"),
    path("artworks/relation-search/", views.artwork_relation_search, name="artwork_relation_search"),
    path("artworks/preview/", views.artwork_preview, name="artwork_preview"),
    path("artworks/attach/", views.artwork_attach, name="artwork_attach"),
    path("artworks/delete/preview/", views.artwork_delete_preview, name="artwork_delete_preview"),
    path("artworks/delete/", views.artwork_delete, name="artwork_delete"),
    path("artworks/<int:uw_id>/quick/", views.artwork_quick, name="artwork_quick"),
    path("artworks/<int:uw_id>/", views.artwork_detail, name="artwork_detail"),
    path("works/<str:type_key>/<int:work_id>/", views.artwork_work, name="artwork_work"),
]
