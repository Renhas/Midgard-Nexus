from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "collections"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="vor_archives:collections:tree", permanent=False
        ),
        name="index",
    ),
    path("tree/", views.collection_tree, name="tree"),
    path("new/", views.collection_new, name="new"),
    path("reorder/", views.collection_reorder, name="reorder"),
    path("<int:pk>/edit/", views.collection_edit, name="edit"),
    path(
        "<int:pk>/delete/preview/",
        views.collection_delete_preview,
        name="delete_preview",
    ),
    path("<int:pk>/delete/", views.collection_delete, name="delete"),
    path(
        "<int:pk>/items/reorder/", views.collection_items_reorder, name="items_reorder"
    ),
    path("<int:pk>/items/", views.collection_items, name="items"),
    path("<int:pk>/", views.collection_update, name="update"),
]
