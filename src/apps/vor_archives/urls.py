from django.urls import include, path

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
    path("artworks/", include("apps.vor_archives.artworks.urls")),
    path("collections/", include("apps.vor_archives.artworks.collections_urls")),
]
