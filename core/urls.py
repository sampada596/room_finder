from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("rooms/", views.browse_rooms, name="browse_rooms"),
    path("ajax/districts/", views.get_districts, name="get_districts"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/listings/pending/", views.dashboard_pending, name="dashboard_pending"),
    path("dashboard/listings/approved/", views.dashboard_approved, name="dashboard_approved"),
    path("dashboard/listings/rejected/", views.dashboard_rejected, name="dashboard_rejected"),
    path("dashboard/listing/<uuid:pk>/review/", views.dashboard_review_listing, name="dashboard_review_listing"),
    path("dashboard/listing/<uuid:pk>/approve/", views.dashboard_approve_listing, name="dashboard_approve_listing"),
    path("dashboard/listing/<uuid:pk>/reject/", views.dashboard_reject_listing, name="dashboard_reject_listing"),
    path("dashboard/users/", views.dashboard_users, name="dashboard_users"),
    path("dashboard/users/<uuid:pk>/toggle/", views.dashboard_toggle_user, name="dashboard_toggle_user"),
    path("contact/submit/", views.contact_submit, name="contact_submit"),

]
