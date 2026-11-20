from django.urls import include, path

from . import views

app_name = "vor_archives"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", include("apps.vor_archives.dashboard.urls")),
    path("attributes/", include("apps.vor_archives.attributes.urls")),
    path("artworks/", include("apps.vor_archives.artworks.urls")),
    path("collections/", include("apps.vor_archives.artworks.collections_urls")),
]
