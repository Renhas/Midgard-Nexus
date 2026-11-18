from django.urls import path

from . import views

app_name = "attributes"

urlpatterns = [
    path("", views.attributes, name="index"),
    path("<str:kind>/list/", views.attr_list, name="list"),
    path("<str:kind>/empty/", views.attr_empty, name="empty"),
    path("<str:kind>/new/", views.attr_new, name="new"),
    path(
        "<str:kind>/delete/preview/",
        views.attr_delete_preview,
        name="delete_preview",
    ),
    path("<str:kind>/delete/", views.attr_delete, name="delete"),
    path(
        "genres/<str:type_key>/<int:pk>/edit/",
        views.genre_edit,
        name="genre_edit",
    ),
    path(
        "genres/<str:type_key>/<int:pk>/",
        views.genre_detail,
        name="genre_detail",
    ),
    path("<str:kind>/<int:pk>/edit/", views.attr_edit, name="edit"),
    path("<str:kind>/<int:pk>/", views.attr_detail, name="detail"),
    path("<str:kind>/", views.attributes_kind, name="kind"),
]
