from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("registration-complete/", views.registration_complete_view, name="registration_complete"),
]