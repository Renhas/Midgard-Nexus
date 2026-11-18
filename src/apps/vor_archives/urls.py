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
    path("attributes/", include("apps.vor_archives.attributes.urls")),
    path("artworks/", include("apps.vor_archives.artworks.urls")),
    path("collections/", include("apps.vor_archives.artworks.collections_urls")),
]
