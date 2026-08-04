from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("verify-otp/resend/", views.resend_otp_view, name="resend_otp"),
    path("registration-complete/", views.registration_complete_view, name="registration_complete"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/", views.reset_password_view, name="reset_password"),
    path("reset-password/resend/", views.resend_reset_code_view, name="resend_reset_code"),
    path("google/login/", views.google_login_view, name="google_login"),
    path("google/callback/", views.google_callback_view, name="google_callback"),
    path("google/complete-profile/", views.google_complete_profile_view, name="google_complete_profile"),
]