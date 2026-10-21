from django.urls import path

from . import views

app_name = "artworks"

urlpatterns = [
    path("", views.artwork_list, name="list"),
    path("new/", views.artwork_add, name="add"),
    path("search/", views.artwork_search, name="search"),
    path("library-search/", views.artwork_library_search, name="library_search"),
    path("reorder/", views.artwork_reorder, name="reorder"),
    path("relation-search/", views.artwork_relation_search, name="relation_search"),
    path("preview/", views.artwork_preview, name="preview"),
    path("attach/", views.artwork_attach, name="attach"),
    path("delete/preview/", views.artwork_delete_preview, name="delete_preview"),
    path("delete/", views.artwork_delete, name="delete"),
    path("<int:uw_id>/quick/", views.artwork_quick, name="quick"),
    path("<int:uw_id>/collections/", views.artwork_collections, name="collections"),
    path("<int:uw_id>/", views.artwork_detail, name="detail"),
    path("<str:type_key>/<int:work_id>/", views.artwork_work, name="work"),
]
