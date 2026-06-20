from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("favourites/toggle/<int:yarn_id>/", views.toggle_favourite, name="toggle_favourite"),
    path("profile/", views.profile, name="profile"),
    path("privacy/", views.privacy, name="privacy"),
    path("robots.txt", views.robots_txt),
]
