from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .forms import RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from .models import User, OTP
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
import requests
import urllib.parse


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone=data["phone"],
                role=data["role"],
            )
            user.is_active = False
            user.save()

            otp = OTP.objects.create(user=user, code=OTP.generate_code())
            send_mail(
                subject="Verify your Room Finder account",
                message=f"Your OTP code is {otp.code}. It expires in 5 minutes.",
                from_email=None,
                recipient_list=[user.email],
            )

            request.session["pending_user_id"] = str(user.id)
            return redirect("verify_otp")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_otp_view(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        messages.error(request, "Please register first.")
        return redirect("register")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        code = request.POST.get("code")
        otp = OTP.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()

        if not otp:
            messages.error(request, "Invalid OTP code.")
        elif otp.is_expired():
            messages.error(request, "This OTP has expired. Please request a new one.")
        else:
            otp.is_used = True
            otp.save()
            user.email_verified = True
            user.is_active = True
            user.save()
            del request.session["pending_user_id"]
            messages.success(request, "Account verified!")
            return redirect("registration_complete")

    return render(request, "accounts/verify_otp.html", {"email": user.email})


def registration_complete_view(request):
    return render(request, "accounts/registration_complete.html")

def resend_otp_view(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        messages.error(request, "Please register first.")
        return redirect("register")
 
    user = User.objects.get(id=user_id)
    otp = OTP.objects.create(user=user, code=OTP.generate_code())
    send_mail(
        subject="Verify your Room Finder account",
        message=f"Your OTP code is {otp.code}. It expires in 5 minutes.",
        from_email=None,
        recipient_list=[user.email],
    )
    messages.success(request, "A new code has been sent to your email.")
    return redirect("verify_otp")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.email_verified:
                messages.error(request, "Please verify your email before logging in.")
                return redirect("login")
            login(request, user)
            if user.role == "landlord":
                return redirect("landlord_dashboard")
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "accounts/login.html", {})

def logout_view(request):
    logout(request)
    return redirect("home")


def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            try:
                user = User.objects.get(email=email)
                otp = OTP.objects.create(user=user, code=OTP.generate_code())
                send_mail(
                    subject="Reset your Room Finder password",
                    message=f"Your password reset code is {otp.code}. It expires in 5 minutes.",
                    from_email=None,
                    recipient_list=[user.email],
                )
                request.session["reset_user_id"] = str(user.id)
            except User.DoesNotExist:
                pass  # don't reveal whether the email exists
            messages.success(request, "If an account exists with that email, a reset code has been sent.")
            return redirect("reset_password")
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form})


def reset_password_view(request):
    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.error(request, "Please request a password reset first.")
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = OTP.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()

            if not otp:
                messages.error(request, "Invalid reset code.")
            elif otp.is_expired():
                messages.error(request, "This code has expired. Please request a new one.")
            else:
                otp.is_used = True
                otp.save()
                user.set_password(form.cleaned_data["new_password"])
                user.save()
                del request.session["reset_user_id"]
                messages.success(request, "Your password has been reset. Please log in.")
                return redirect("login")
    else:
        form = ResetPasswordForm()

    return render(request, "accounts/reset_password.html", {"form": form, "email": user.email})


def resend_reset_code_view(request):
    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.error(request, "Please request a password reset first.")
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)
    otp = OTP.objects.create(user=user, code=OTP.generate_code())
    send_mail(
        subject="Reset your Room Finder password",
        message=f"Your password reset code is {otp.code}. It expires in 5 minutes.",
        from_email=None,
        recipient_list=[user.email],
    )
    messages.success(request, "A new code has been sent to your email.")
    return redirect("reset_password")

def google_login_view(request):
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(google_auth_url)


def google_callback_view(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error or not code:
        messages.error(request, "Google sign-in was cancelled or failed.")
        return redirect("login")

    token_response = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    })

    if token_response.status_code != 200:
        messages.error(request, "Couldn't verify your Google account. Please try again.")
        return redirect("login")

    access_token = token_response.json().get("access_token")

    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if userinfo_response.status_code != 200:
        messages.error(request, "Couldn't fetch your Google profile. Please try again.")
        return redirect("login")

    profile = userinfo_response.json()
    email = profile.get("email", "").lower()
    first_name = profile.get("given_name", "")
    last_name = profile.get("family_name", "")

    if not email:
        messages.error(request, "Google didn't share an email address. Please try a different sign-in method.")
        return redirect("login")

    try:
        user = User.objects.get(email=email)
        user.email_verified = True
        user.save()
        login(request, user)
        return redirect("home")
    except User.DoesNotExist:
        request.session["google_pending"] = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        return redirect("google_complete_profile")


def google_complete_profile_view(request):
    pending = request.session.get("google_pending")
    if not pending:
        messages.error(request, "Your Google sign-in session expired. Please try again.")
        return redirect("login")

    if request.method == "POST":
        role = request.POST.get("role")
        phone = request.POST.get("phone", "").strip()

        if role not in ("tenant", "landlord") or not phone:
            messages.error(request, "Please select a role and enter your phone number.")
        else:
            user = User.objects.create(
                email=pending["email"],
                first_name=pending["first_name"],
                last_name=pending["last_name"],
                phone=phone,
                role=role,
                email_verified=True,
            )
            user.set_unusable_password()
            user.save()
            del request.session["google_pending"]
            login(request, user)
            messages.success(request, "Welcome to Basera!")
            return redirect("home")

    return render(request, "accounts/google_complete_profile.html", {"pending": pending})
