from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="index"),
    path("activity/feed/", views.dashboard_feed, name="feed"),
    path("activity/heatmap/", views.dashboard_heatmap, name="heatmap"),
    path("<str:tab>/", views.dashboard_tab, name="tab"),
]
