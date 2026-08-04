from django.urls import path
from . import views

urlpatterns = [
    path("create/step1/", views.listing_step1, name="listing_step1"),
    path("create/step2/", views.listing_step2, name="listing_step2"),
    path("create/step3/", views.listing_step3, name="listing_step3"),
    path("create/step4/", views.listing_step4, name="listing_step4"),
    path("create/step5/", views.listing_step5, name="listing_step5"),
    path("submitted/", views.listing_submitted, name="listing_submitted"),
    path("<uuid:pk>/", views.listing_detail, name="listing_detail"),
    path("<uuid:pk>/reveal-phone/", views.reveal_phone, name="reveal_phone"),
    path("<uuid:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("<uuid:pk>/report/", views.report_listing, name="report_listing"),
    path("<uuid:pk>/request/", views.request_to_rent, name="request_to_rent"),
    path("favorites/", views.my_favorites, name="my_favorites"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("my-listings/", views.landlord_dashboard, name="landlord_dashboard"),
    path("requests/", views.landlord_requests, name="landlord_requests"),
    path("requests/<int:pk>/respond/", views.respond_to_request, name="respond_to_request"),
]
