from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .forms import RegistrationForm
from .models import User, OTP


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