from django.urls import path

from . import views

app_name = "vor_archives"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/activity/feed/", views.dashboard_feed, name="dashboard_feed"),
    path(
        "dashboard/activity/heatmap/",
        views.dashboard_heatmap,
        name="dashboard_heatmap",
    ),
    path("dashboard/<str:tab>/", views.dashboard_tab, name="dashboard_tab"),
    path("attributes/", views.attributes, name="attributes"),
    path("attributes/<str:kind>/list/", views.attr_list, name="attr_list"),
    path("attributes/<str:kind>/empty/", views.attr_empty, name="attr_empty"),
    path("attributes/<str:kind>/new/", views.attr_new, name="attr_new"),
    path(
        "attributes/<str:kind>/delete/preview/",
        views.attr_delete_preview,
        name="attr_delete_preview",
    ),
    path("attributes/<str:kind>/delete/", views.attr_delete, name="attr_delete"),
    path(
        "attributes/genres/<str:type_key>/<int:pk>/edit/",
        views.genre_edit,
        name="genre_edit",
    ),
    path(
        "attributes/genres/<str:type_key>/<int:pk>/",
        views.genre_detail,
        name="genre_detail",
    ),
    path("attributes/<str:kind>/<int:pk>/edit/", views.attr_edit, name="attr_edit"),
    path("attributes/<str:kind>/<int:pk>/", views.attr_detail, name="attr_detail"),
    path("attributes/<str:kind>/", views.attributes_kind, name="attributes_kind"),
    path("artworks/", views.artwork_list, name="artwork_list"),
    path("artworks/new/", views.artwork_add, name="artwork_add"),
    path("artworks/search/", views.artwork_search, name="artwork_search"),
    path(
        "artworks/library-search/",
        views.artwork_library_search,
        name="artwork_library_search",
    ),
    path("artworks/reorder/", views.artwork_reorder, name="artwork_reorder"),
    path(
        "artworks/relation-search/",
        views.artwork_relation_search,
        name="artwork_relation_search",
    ),
    path("artworks/preview/", views.artwork_preview, name="artwork_preview"),
    path("artworks/attach/", views.artwork_attach, name="artwork_attach"),
    path(
        "artworks/delete/preview/",
        views.artwork_delete_preview,
        name="artwork_delete_preview",
    ),
    path("artworks/delete/", views.artwork_delete, name="artwork_delete"),
    path("artworks/<int:uw_id>/quick/", views.artwork_quick, name="artwork_quick"),
    path(
        "artworks/<int:uw_id>/collections/",
        views.artwork_collections,
        name="artwork_collections",
    ),
    path("artworks/<int:uw_id>/", views.artwork_detail, name="artwork_detail"),
    path("collections/tree/", views.collection_tree, name="collection_tree"),
    path("collections/new/", views.collection_new, name="collection_new"),
    path("collections/reorder/", views.collection_reorder, name="collection_reorder"),
    path("collections/<int:pk>/edit/", views.collection_edit, name="collection_edit"),
    path(
        "collections/<int:pk>/delete/",
        views.collection_delete,
        name="collection_delete",
    ),
    path(
        "collections/<int:pk>/delete/preview/",
        views.collection_delete_preview,
        name="collection_delete_preview",
    ),
    path(
        "collections/<int:pk>/items/reorder/",
        views.collection_items_reorder,
        name="collection_items_reorder",
    ),
    path(
        "collections/<int:pk>/items/", views.collection_items, name="collection_items"
    ),
    path("collections/<int:pk>/", views.collection_update, name="collection_update"),
    path(
        "works/<str:type_key>/<int:work_id>/", views.artwork_work, name="artwork_work"
    ),
]
