from django.urls import path
from . import views

urlpatterns = [
    path("ajax/districts/", views.get_districts, name="get_districts"),
]